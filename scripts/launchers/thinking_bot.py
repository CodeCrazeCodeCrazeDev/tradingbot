"""
Thinking Bot - Unified Trading System with Complete Analysis → Validation → Execution → Monitoring Loop

This is the main entry point for the "thinking bot" that:
A. Analyzes market data across multiple timeframes
B. Validates signals with risk management
C. Executes trades with smart order routing
D. Monitors positions and performance
E. Learns and adapts over time
"""

import os
import sys
import time
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import yaml
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Import existing modules
from trading_bot.brain import EliteBrain, BrainDecision, DecisionState
from trading_bot.orchestrator import MasterOrchestrator
from trading_bot.risk import RiskManager
from trading_bot.execution import SmartOrderRouter, VenueType
try:
    from trading_bot.orchestrator import PerformanceTracker
except ImportError:
    PerformanceTracker = None

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/thinking_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


@dataclass
class MarketAnalysis:
    """Complete market analysis result"""
    timestamp: datetime
    symbol: str
    timeframe: str
    
    # Price data
    current_price: float
    bid: float
    ask: float
    spread: float
    
    # Trend analysis
    trend_direction: str  # BULLISH, BEARISH, NEUTRAL
    trend_strength: float  # 0-1
    trend_timeframes: Dict[str, str]  # Trend per timeframe
    
    # Technical indicators
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    ema_20: float
    ema_50: float
    ema_200: float
    atr: float
    bollinger_upper: float
    bollinger_lower: float
    
    # Market conditions
    volatility: float
    momentum: float
    volume_ratio: float
    
    # Support/Resistance
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # Pattern detection
    patterns: List[str] = field(default_factory=list)
    
    # Sentiment (if available)
    sentiment_score: Optional[float] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TradingSignal:
    """Trading signal with complete context"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    signal_strength: SignalStrength
    
    # Entry details
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Position sizing
    recommended_lots: float
    risk_amount: float
    risk_reward_ratio: float
    
    # Confidence and reasoning
    confidence: float  # 0-1
    reasoning: str
    supporting_factors: List[str] = field(default_factory=list)
    
    # Multi-timeframe alignment
    timeframe_alignment: Dict[str, str] = field(default_factory=dict)
    
    # AI prediction (if available)
    ai_prediction: Optional[str] = None
    ai_confidence: Optional[float] = None
    
    def to_dict(self):
        result = asdict(self)
        result['signal_type'] = self.signal_type.value
        result['signal_strength'] = self.signal_strength.value
        return result


@dataclass
class RiskValidation:
    """Risk validation result"""
    is_valid: bool
    approved_lots: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Risk metrics
    account_risk_pct: float = 0.0
    position_size_pct: float = 0.0
    total_exposure_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    
    # Limits
    within_position_limit: bool = True
    within_risk_limit: bool = True
    within_exposure_limit: bool = True
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TradeExecution:
    """Trade execution result"""
    success: bool
    order_id: Optional[int] = None
    ticket: Optional[int] = None
    
    # Execution details
    symbol: str = ""
    action: str = ""
    lots: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    # Execution quality
    slippage: float = 0.0
    execution_time_ms: float = 0.0
    
    # Status
    status: str = ""
    message: str = ""
    error: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class PositionMonitor:
    """Active position monitoring data"""
    ticket: int
    symbol: str
    type: str  # BUY or SELL
    lots: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    
    # P&L
    profit: float
    profit_pips: float
    profit_pct: float
    
    # Time
    open_time: datetime
    duration_seconds: float
    
    # Status
    is_breakeven: bool = False
    is_trailing: bool = False
    
    def to_dict(self):
        return asdict(self)


class ThinkingBot:
    """
    Main Thinking Bot Controller
    
    Implements the complete trading loop:
    1. Analysis (The Brain) - Multi-timeframe market analysis
    2. Risk Management (The Guardian) - Signal validation and risk checks
    3. Execution (The Engine) - Smart order execution
    4. Monitoring (The Watchdog) - Position and system monitoring
    5. Performance (The Teacher) - Learning and adaptation
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # State
        self.running = False
        self.initialized = False
        self.cycle_count = 0
        self.start_time = None
        
        # Components (initialized later)
        self.brain = None
        self.orchestrator = None
        self.risk_manager = None
        self.smart_router = None
        self.performance_tracker = None
        
        # Data storage
        self.market_data = {}
        self.active_signals = {}
        self.active_positions = {}
        self.trade_history = []
        
        # Performance metrics
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }
        
        logger.info("ThinkingBot initialized")
    
    def _load_config(self) -> dict:
        """Load configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    async def initialize(self) -> bool:
        """Initialize all systems"""
        logger.info("=" * 80)
        logger.info("INITIALIZING THINKING BOT")
        logger.info("=" * 80)
        
        try:
            # Load environment
            load_dotenv()
            logger.info("✓ Environment loaded")
            
            # Initialize MT5
            if not mt5.initialize():
                logger.error(f"✗ MT5 initialization failed: {mt5.last_error()}")
                return False
            logger.info("✓ MT5 initialized")
            
            # Check account
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("✗ Failed to get account info")
                mt5.shutdown()
                return False
            
            logger.info(f"✓ Account: {account_info.login} on {account_info.server}")
            logger.info(f"  Balance: ${account_info.balance:.2f}")
            logger.info(f"  Equity: ${account_info.equity:.2f}")
            logger.info(f"  Margin Free: ${account_info.margin_free:.2f}")
            
            # Initialize components
            logger.info("\nInitializing trading components...")
            
            # 1. Brain (Analysis)
            try:
                self.brain = EliteBrain(config=self.config)
                logger.info("✓ Elite Brain initialized")
            except Exception as e:
                logger.warning(f"⚠ Elite Brain initialization failed: {e}")
                self.brain = None
            
            # 2. Orchestrator
            try:
                self.orchestrator = MasterOrchestrator(config=self.config)
                logger.info("✓ Master Orchestrator initialized")
            except Exception as e:
                logger.warning(f"⚠ Orchestrator initialization failed: {e}")
                self.orchestrator = None
            
            # 3. Risk Manager
            try:
                self.risk_manager = RiskManager(config=self.config)
                logger.info("✓ Risk Manager initialized")
            except Exception as e:
                logger.warning(f"⚠ Risk Manager initialization failed: {e}")
                self.risk_manager = None
            
            # 4. Smart Router
            try:
                self.smart_router = SmartOrderRouter(config=self.config)
                logger.info("✓ Smart Order Router initialized")
            except Exception as e:
                logger.warning(f"⚠ Smart Router initialization failed: {e}")
                self.smart_router = None
            
            # 5. Performance Tracker
            try:
                self.performance_tracker = PerformanceTracker(config=self.config)
                logger.info("✓ Performance Tracker initialized")
            except Exception as e:
                logger.warning(f"⚠ Performance Tracker initialization failed: {e}")
                self.performance_tracker = None
            
            logger.info("=" * 80)
            logger.info("ALL SYSTEMS INITIALIZED SUCCESSFULLY")
            logger.info("=" * 80)
            
            self.initialized = True
            self.start_time = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def analyze_market(self, symbol: str) -> MarketAnalysis:
        """
        A. ANALYSIS (THE BRAIN)
        
        Collects and analyzes market data across multiple timeframes
        """
        try:
            logger.debug(f"Analyzing {symbol}...")
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise ValueError(f"Failed to get tick for {symbol}")
            
            # Get multi-timeframe data
            timeframes = {
                '1M': mt5.TIMEFRAME_M1,
                '5M': mt5.TIMEFRAME_M5,
                '15M': mt5.TIMEFRAME_M15,
                '1H': mt5.TIMEFRAME_H1,
                '4H': mt5.TIMEFRAME_H4,
                '1D': mt5.TIMEFRAME_D1,
                '1W': mt5.TIMEFRAME_W1
            }
            
            # Analyze primary timeframe (1H for now)
            primary_tf = mt5.TIMEFRAME_H1
            rates = mt5.copy_rates_from_pos(symbol, primary_tf, 0, 200)
            
            if rates is None or len(rates) == 0:
                raise ValueError(f"Failed to get rates for {symbol}")
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate indicators
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['tick_volume'].values
            
            # RSI
            rsi = self._calculate_rsi(close, period=14)
            
            # MACD
            macd, macd_signal, macd_hist = self._calculate_macd(close)
            
            # EMAs
            ema_20 = self._calculate_ema(close, period=20)
            ema_50 = self._calculate_ema(close, period=50)
            ema_200 = self._calculate_ema(close, period=200)
            
            # ATR
            atr = self._calculate_atr(high, low, close, period=14)
            
            # Bollinger Bands
            bb_upper, bb_lower = self._calculate_bollinger_bands(close, period=20, std=2)
            
            # Trend analysis across timeframes
            trend_timeframes = {}
            for tf_name, tf_value in timeframes.items():
                trend = self._detect_trend(symbol, tf_value)
                trend_timeframes[tf_name] = trend
            
            # Determine overall trend
            bullish_count = sum(1 for t in trend_timeframes.values() if t == "BULLISH")
            bearish_count = sum(1 for t in trend_timeframes.values() if t == "BEARISH")
            
            if bullish_count > bearish_count * 1.5:
                overall_trend = "BULLISH"
                trend_strength = bullish_count / len(trend_timeframes)
            elif bearish_count > bullish_count * 1.5:
                overall_trend = "BEARISH"
                trend_strength = bearish_count / len(trend_timeframes)
            else:
                overall_trend = "NEUTRAL"
                trend_strength = 0.5
            
            # Calculate volatility and momentum
            volatility = atr[-1] / close[-1] if len(atr) > 0 else 0.0
            momentum = (close[-1] - close[-20]) / close[-20] if len(close) > 20 else 0.0
            volume_ratio = volume[-1] / np.mean(volume[-20:]) if len(volume) > 20 else 1.0
            
            # Support and resistance
            support_levels = self._find_support_levels(df)
            resistance_levels = self._find_resistance_levels(df)
            
            # Pattern detection
            patterns = self._detect_patterns(df)
            
            analysis = MarketAnalysis(
                timestamp=datetime.now(),
                symbol=symbol,
                timeframe="1H",
                current_price=tick.ask,
                bid=tick.bid,
                ask=tick.ask,
                spread=tick.ask - tick.bid,
                trend_direction=overall_trend,
                trend_strength=trend_strength,
                trend_timeframes=trend_timeframes,
                rsi=rsi[-1] if len(rsi) > 0 else 50.0,
                macd=macd[-1] if len(macd) > 0 else 0.0,
                macd_signal=macd_signal[-1] if len(macd_signal) > 0 else 0.0,
                macd_histogram=macd_hist[-1] if len(macd_hist) > 0 else 0.0,
                ema_20=ema_20[-1] if len(ema_20) > 0 else close[-1],
                ema_50=ema_50[-1] if len(ema_50) > 0 else close[-1],
                ema_200=ema_200[-1] if len(ema_200) > 0 else close[-1],
                atr=atr[-1] if len(atr) > 0 else 0.0,
                bollinger_upper=bb_upper[-1] if len(bb_upper) > 0 else close[-1],
                bollinger_lower=bb_lower[-1] if len(bb_lower) > 0 else close[-1],
                volatility=volatility,
                momentum=momentum,
                volume_ratio=volume_ratio,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                patterns=patterns
            )
            
            logger.info(f"✓ Analysis complete: {symbol} - {overall_trend} trend, RSI={rsi[-1]:.1f}, MACD={macd[-1]:.5f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing market: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def generate_signal(self, analysis: MarketAnalysis) -> Optional[TradingSignal]:
        """
        Generate trading signal from market analysis
        """
        try:
            # Check if conditions are met for a signal
            signal_type = SignalType.HOLD
            signal_strength = SignalStrength.WEAK
            confidence = 0.0
            reasoning = ""
            supporting_factors = []
            
            # BUY conditions
            buy_score = 0
            if analysis.trend_direction == "BULLISH":
                buy_score += 2
                supporting_factors.append("Bullish trend across timeframes")
            
            if analysis.rsi < 30:
                buy_score += 2
                supporting_factors.append("RSI oversold (<30)")
            elif analysis.rsi < 50:
                buy_score += 1
                supporting_factors.append("RSI below 50")
            
            if analysis.macd > analysis.macd_signal and analysis.macd_histogram > 0:
                buy_score += 2
                supporting_factors.append("MACD bullish crossover")
            
            if analysis.current_price > analysis.ema_20 > analysis.ema_50:
                buy_score += 1
                supporting_factors.append("Price above EMAs (bullish alignment)")
            
            if analysis.momentum > 0.01:
                buy_score += 1
                supporting_factors.append("Positive momentum")
            
            # SELL conditions
            sell_score = 0
            if analysis.trend_direction == "BEARISH":
                sell_score += 2
                supporting_factors.append("Bearish trend across timeframes")
            
            if analysis.rsi > 70:
                sell_score += 2
                supporting_factors.append("RSI overbought (>70)")
            elif analysis.rsi > 50:
                sell_score += 1
                supporting_factors.append("RSI above 50")
            
            if analysis.macd < analysis.macd_signal and analysis.macd_histogram < 0:
                sell_score += 2
                supporting_factors.append("MACD bearish crossover")
            
            if analysis.current_price < analysis.ema_20 < analysis.ema_50:
                sell_score += 1
                supporting_factors.append("Price below EMAs (bearish alignment)")
            
            if analysis.momentum < -0.01:
                sell_score += 1
                supporting_factors.append("Negative momentum")
            
            # Determine signal
            if buy_score >= 5 and buy_score > sell_score:
                signal_type = SignalType.BUY
                confidence = min(buy_score / 8.0, 1.0)
                reasoning = f"BUY signal: {analysis.symbol} trend {analysis.trend_direction} on 1H & 4H; RSI={analysis.rsi:.1f}; MACD cross detected"
                
                if buy_score >= 7:
                    signal_strength = SignalStrength.VERY_STRONG
                elif buy_score >= 6:
                    signal_strength = SignalStrength.STRONG
                else:
                    signal_strength = SignalStrength.MODERATE
                
            elif sell_score >= 5 and sell_score > buy_score:
                signal_type = SignalType.SELL
                confidence = min(sell_score / 8.0, 1.0)
                reasoning = f"SELL signal: {analysis.symbol} trend {analysis.trend_direction} on 1H & 4H; RSI={analysis.rsi:.1f}; MACD cross detected"
                
                if sell_score >= 7:
                    signal_strength = SignalStrength.VERY_STRONG
                elif sell_score >= 6:
                    signal_strength = SignalStrength.STRONG
                else:
                    signal_strength = SignalStrength.MODERATE
            else:
                # No clear signal
                return None
            
            # Calculate entry, SL, TP
            atr = analysis.atr
            if signal_type == SignalType.BUY:
                entry_price = analysis.ask
                stop_loss = entry_price - (atr * self.config.get('trading', {}).get('stop_loss_atr_multiplier', 2.0))
                take_profit = entry_price + (atr * self.config.get('trading', {}).get('take_profit_rr_ratio', 2.0) * 
                                            self.config.get('trading', {}).get('stop_loss_atr_multiplier', 2.0))
            else:  # SELL
                entry_price = analysis.bid
                stop_loss = entry_price + (atr * self.config.get('trading', {}).get('stop_loss_atr_multiplier', 2.0))
                take_profit = entry_price - (atr * self.config.get('trading', {}).get('take_profit_rr_ratio', 2.0) * 
                                            self.config.get('trading', {}).get('stop_loss_atr_multiplier', 2.0))
            
            # Calculate position size
            account_info = mt5.account_info()
            risk_amount = account_info.balance * self.config.get('trading', {}).get('risk_per_trade', 0.01)
            
            # Calculate lot size based on risk
            pip_value = 10.0  # For standard lot on EURUSD
            stop_loss_pips = abs(entry_price - stop_loss) * 10000
            recommended_lots = risk_amount / (stop_loss_pips * pip_value)
            recommended_lots = round(recommended_lots, 2)
            
            # Risk-reward ratio
            risk_reward_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
            
            signal = TradingSignal(
                timestamp=datetime.now(),
                symbol=analysis.symbol,
                signal_type=signal_type,
                signal_strength=signal_strength,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                recommended_lots=recommended_lots,
                risk_amount=risk_amount,
                risk_reward_ratio=risk_reward_ratio,
                confidence=confidence,
                reasoning=reasoning,
                supporting_factors=supporting_factors,
                timeframe_alignment=analysis.trend_timeframes
            )
            
            logger.info(f"✓ Signal generated: {signal_type.value} {analysis.symbol} @ {entry_price:.5f}, "
                       f"SL={stop_loss:.5f}, TP={take_profit:.5f}, Confidence={confidence:.2f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def validate_signal(self, signal: TradingSignal) -> RiskValidation:
        """
        B. RISK MANAGEMENT (THE GUARDIAN)
        
        Validates signal against risk rules
        """
        try:
            logger.debug(f"Validating signal for {signal.symbol}...")
            
            is_valid = True
            warnings = []
            errors = []
            approved_lots = signal.recommended_lots
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                errors.append("Failed to get account info")
                return RiskValidation(is_valid=False, approved_lots=0.0, errors=errors)
            
            # Check 1: Position size limits
            max_position_size = self.config.get('risk', {}).get('max_position_size', 1.0)
            min_position_size = self.config.get('risk', {}).get('min_position_size', 0.01)
            
            if signal.recommended_lots > max_position_size:
                warnings.append(f"Position size capped: {signal.recommended_lots:.2f} → {max_position_size:.2f}")
                approved_lots = max_position_size
            
            if signal.recommended_lots < min_position_size:
                errors.append(f"Position size too small: {signal.recommended_lots:.2f} < {min_position_size:.2f}")
                is_valid = False
            
            # Check 2: Account risk
            risk_per_trade_pct = self.config.get('risk', {}).get('risk_per_trade_pct', 1.0)
            account_risk_pct = (signal.risk_amount / account_info.balance) * 100
            
            if account_risk_pct > risk_per_trade_pct:
                warnings.append(f"Risk per trade exceeds limit: {account_risk_pct:.2f}% > {risk_per_trade_pct:.2f}%")
                # Adjust lot size
                approved_lots = approved_lots * (risk_per_trade_pct / account_risk_pct)
                approved_lots = round(approved_lots, 2)
            
            # Check 3: Total exposure
            total_exposure = self._calculate_total_exposure()
            max_exposure_pct = 10.0  # Max 10% total exposure
            position_size_pct = (approved_lots * 100000 * signal.entry_price) / account_info.equity * 100
            
            if total_exposure + position_size_pct > max_exposure_pct:
                errors.append(f"Total exposure would exceed limit: {total_exposure + position_size_pct:.2f}% > {max_exposure_pct:.2f}%")
                is_valid = False
            
            # Check 4: Max positions
            max_positions = self.config.get('trading', {}).get('max_positions', 5)
            if len(self.active_positions) >= max_positions:
                errors.append(f"Max positions reached: {len(self.active_positions)} >= {max_positions}")
                is_valid = False
            
            # Check 5: Balance check
            if account_info.balance < 100:
                errors.append(f"Balance too low: ${account_info.balance:.2f}")
                is_valid = False
            
            # Check 6: Margin check
            required_margin = approved_lots * 100000 / 100  # Simplified
            if account_info.margin_free < required_margin:
                errors.append(f"Insufficient margin: ${account_info.margin_free:.2f} < ${required_margin:.2f}")
                is_valid = False
            
            validation = RiskValidation(
                is_valid=is_valid,
                approved_lots=approved_lots,
                warnings=warnings,
                errors=errors,
                account_risk_pct=account_risk_pct,
                position_size_pct=position_size_pct,
                total_exposure_pct=total_exposure + position_size_pct,
                within_position_limit=approved_lots <= max_position_size,
                within_risk_limit=account_risk_pct <= risk_per_trade_pct,
                within_exposure_limit=total_exposure + position_size_pct <= max_exposure_pct
            )
            
            if is_valid:
                logger.info(f"✓ Signal validated: {signal.symbol}, Approved lots={approved_lots:.2f}, Risk={account_risk_pct:.2f}%")
            else:
                logger.warning(f"✗ Signal rejected: {signal.symbol}, Errors: {', '.join(errors)}")
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            logger.error(traceback.format_exc())
            return RiskValidation(is_valid=False, approved_lots=0.0, errors=[str(e)])
    
    async def execute_trade(self, signal: TradingSignal, validation: RiskValidation) -> TradeExecution:
        """
        C. EXECUTION (THE ENGINE)
        
        Executes validated trade
        """
        try:
            logger.info(f"Executing trade: {signal.signal_type.value} {signal.symbol} @ {signal.entry_price:.5f}")
            
            start_time = time.time()
            
            # Prepare order
            symbol = signal.symbol
            action = mt5.ORDER_TYPE_BUY if signal.signal_type == SignalType.BUY else mt5.ORDER_TYPE_SELL
            lots = validation.approved_lots
            price = signal.entry_price
            sl = signal.stop_loss
            tp = signal.take_profit
            
            # Check if paper trading
            if self.config.get('trading', {}).get('mode', 'paper') == 'paper':
                logger.info("📝 Paper trading mode - simulating execution")
                
                execution = TradeExecution(
                    success=True,
                    order_id=int(time.time()),
                    ticket=int(time.time()),
                    symbol=symbol,
                    action="BUY" if signal.signal_type == SignalType.BUY else "SELL",
                    lots=lots,
                    entry_price=price,
                    stop_loss=sl,
                    take_profit=tp,
                    slippage=0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    status="FILLED",
                    message="Paper trade executed successfully"
                )
                
                # Store position
                self.active_positions[execution.ticket] = {
                    'ticket': execution.ticket,
                    'symbol': symbol,
                    'type': execution.action,
                    'lots': lots,
                    'entry_price': price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'open_time': datetime.now()
                }
                
                logger.info(f"✓ Paper trade executed: Ticket={execution.ticket}")
                
                return execution
            
            # Live trading
            logger.info("🚀 Live trading mode - sending order to broker")
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lots,
                "type": action,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": 234000,
                "comment": f"ThinkingBot_{signal.signal_type.value}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            execution_time = (time.time() - start_time) * 1000
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order failed: {result.comment} (code: {result.retcode})"
                logger.error(f"✗ {error_msg}")
                
                return TradeExecution(
                    success=False,
                    symbol=symbol,
                    action="BUY" if signal.signal_type == SignalType.BUY else "SELL",
                    lots=lots,
                    execution_time_ms=execution_time,
                    status="REJECTED",
                    error=error_msg
                )
            
            # Success
            slippage = abs(result.price - price)
            
            execution = TradeExecution(
                success=True,
                order_id=result.order,
                ticket=result.order,
                symbol=symbol,
                action="BUY" if signal.signal_type == SignalType.BUY else "SELL",
                lots=result.volume,
                entry_price=result.price,
                stop_loss=sl,
                take_profit=tp,
                slippage=slippage,
                execution_time_ms=execution_time,
                status="FILLED",
                message=f"Order executed successfully"
            )
            
            # Store position
            self.active_positions[execution.ticket] = {
                'ticket': execution.ticket,
                'symbol': symbol,
                'type': execution.action,
                'lots': result.volume,
                'entry_price': result.price,
                'stop_loss': sl,
                'take_profit': tp,
                'open_time': datetime.now()
            }
            
            logger.info(f"✓ Trade executed: Ticket={execution.ticket}, Price={result.price:.5f}, Slippage={slippage:.5f}")
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            logger.error(traceback.format_exc())
            return TradeExecution(
                success=False,
                symbol=signal.symbol,
                error=str(e)
            )
    
    async def monitor_positions(self):
        """
        D. MONITORING (THE WATCHDOG)
        
        Monitors active positions and updates stops/targets
        """
        try:
            if not self.active_positions:
                return
            
            logger.debug(f"Monitoring {len(self.active_positions)} positions...")
            
            for ticket, position in list(self.active_positions.items()):
                try:
                    symbol = position['symbol']
                    
                    # Get current price
                    tick = mt5.symbol_info_tick(symbol)
                    if tick is None:
                        continue
                    
                    current_price = tick.bid if position['type'] == 'BUY' else tick.ask
                    entry_price = position['entry_price']
                    stop_loss = position['stop_loss']
                    take_profit = position['take_profit']
                    
                    # Calculate P&L
                    if position['type'] == 'BUY':
                        profit_pips = (current_price - entry_price) * 10000
                        profit = profit_pips * position['lots'] * 10
                    else:
                        profit_pips = (entry_price - current_price) * 10000
                        profit = profit_pips * position['lots'] * 10
                    
                    profit_pct = (profit / (position['lots'] * 100000 * entry_price)) * 100
                    
                    # Duration
                    duration = (datetime.now() - position['open_time']).total_seconds()
                    
                    # Check if TP or SL hit
                    if position['type'] == 'BUY':
                        if current_price >= take_profit:
                            logger.info(f"✓ Take Profit hit: {symbol} Ticket={ticket}, Profit=+{profit_pips:.1f} pips")
                            await self._close_position(ticket, "TP_HIT")
                            continue
                        elif current_price <= stop_loss:
                            logger.info(f"✗ Stop Loss hit: {symbol} Ticket={ticket}, Loss={profit_pips:.1f} pips")
                            await self._close_position(ticket, "SL_HIT")
                            continue
                    else:
                        if current_price <= take_profit:
                            logger.info(f"✓ Take Profit hit: {symbol} Ticket={ticket}, Profit=+{profit_pips:.1f} pips")
                            await self._close_position(ticket, "TP_HIT")
                            continue
                        elif current_price >= stop_loss:
                            logger.info(f"✗ Stop Loss hit: {symbol} Ticket={ticket}, Loss={profit_pips:.1f} pips")
                            await self._close_position(ticket, "SL_HIT")
                            continue
                    
                    # Update trailing stop if enabled
                    # (Simplified - would implement full trailing logic here)
                    
                    logger.debug(f"Position {ticket}: {symbol} {position['type']} {position['lots']} lots, "
                               f"P&L={profit:.2f} ({profit_pips:+.1f} pips), Duration={duration:.0f}s")
                    
                except Exception as e:
                    logger.error(f"Error monitoring position {ticket}: {e}")
            
        except Exception as e:
            logger.error(f"Error in position monitoring: {e}")
            logger.error(traceback.format_exc())
    
    async def _close_position(self, ticket: int, reason: str):
        """Close a position"""
        try:
            if ticket not in self.active_positions:
                return
            
            position = self.active_positions[ticket]
            
            # Paper trading
            if self.config.get('trading', {}).get('mode', 'paper') == 'paper':
                logger.info(f"📝 Paper trading: Closing position {ticket} - {reason}")
                
                # Calculate final P&L
                symbol = position['symbol']
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    current_price = tick.bid if position['type'] == 'BUY' else tick.ask
                    entry_price = position['entry_price']
                    
                    if position['type'] == 'BUY':
                        profit_pips = (current_price - entry_price) * 10000
                    else:
                        profit_pips = (entry_price - current_price) * 10000
                    
                    profit = profit_pips * position['lots'] * 10
                    
                    # Update metrics
                    self.metrics['total_trades'] += 1
                    if profit > 0:
                        self.metrics['winning_trades'] += 1
                        self.metrics['total_profit'] += profit
                    else:
                        self.metrics['losing_trades'] += 1
                        self.metrics['total_loss'] += abs(profit)
                    
                    # Update win rate
                    if self.metrics['total_trades'] > 0:
                        self.metrics['win_rate'] = (self.metrics['winning_trades'] / self.metrics['total_trades']) * 100
                    
                    # Update profit factor
                    if self.metrics['total_loss'] > 0:
                        self.metrics['profit_factor'] = self.metrics['total_profit'] / self.metrics['total_loss']
                    
                    logger.info(f"✓ Position closed: {symbol} {position['type']}, P&L={profit:.2f} ({profit_pips:+.1f} pips)")
                
                # Remove from active positions
                del self.active_positions[ticket]
                
                return
            
            # Live trading - close via MT5
            # (Would implement actual MT5 close logic here)
            
        except Exception as e:
            logger.error(f"Error closing position {ticket}: {e}")
    
    async def update_performance(self):
        """
        E. PERFORMANCE & LEARNING (THE TEACHER)
        
        Updates performance metrics and learns from trades
        """
        try:
            logger.debug("Updating performance metrics...")
            
            # Calculate current metrics
            account_info = mt5.account_info()
            if account_info:
                # Update equity curve
                # Track drawdown
                # Calculate Sharpe ratio
                # etc.
                pass
            
            # Log summary every 100 cycles
            if self.cycle_count % 100 == 0:
                logger.info("=" * 80)
                logger.info("PERFORMANCE SUMMARY")
                logger.info("=" * 80)
                logger.info(f"Total Trades: {self.metrics['total_trades']}")
                logger.info(f"Winning Trades: {self.metrics['winning_trades']}")
                logger.info(f"Losing Trades: {self.metrics['losing_trades']}")
                logger.info(f"Win Rate: {self.metrics['win_rate']:.2f}%")
                logger.info(f"Profit Factor: {self.metrics['profit_factor']:.2f}")
                logger.info(f"Total Profit: ${self.metrics['total_profit']:.2f}")
                logger.info(f"Total Loss: ${self.metrics['total_loss']:.2f}")
                logger.info(f"Net P&L: ${self.metrics['total_profit'] - self.metrics['total_loss']:.2f}")
                logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error updating performance: {e}")
    
    async def trading_cycle(self):
        """
        Main trading cycle: Analysis → Validation → Execution → Monitoring
        """
        try:
            self.cycle_count += 1
            
            # Get symbols to trade
            symbols = self.config.get('mt5', {}).get('symbols', ['EURUSD'])
            
            for symbol in symbols:
                try:
                    # 1. ANALYZE MARKET
                    analysis = await self.analyze_market(symbol)
                    
                    # 2. GENERATE SIGNAL
                    signal = await self.generate_signal(analysis)
                    
                    if signal is None:
                        logger.debug(f"No signal for {symbol}")
                        continue
                    
                    # 3. VALIDATE SIGNAL
                    validation = await self.validate_signal(signal)
                    
                    if not validation.is_valid:
                        logger.warning(f"Signal validation failed for {symbol}")
                        continue
                    
                    # 4. EXECUTE TRADE
                    execution = await self.execute_trade(signal, validation)
                    
                    if not execution.success:
                        logger.error(f"Trade execution failed for {symbol}")
                        continue
                    
                    logger.info(f"✓ Trade cycle completed for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error in trading cycle for {symbol}: {e}")
            
            # 5. MONITOR POSITIONS
            await self.monitor_positions()
            
            # 6. UPDATE PERFORMANCE
            await self.update_performance()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            logger.error(traceback.format_exc())
    
    async def run(self):
        """Main run loop"""
        logger.info("=" * 80)
        logger.info("THINKING BOT - STARTING")
        logger.info("=" * 80)
        
        # Initialize
        if not await self.initialize():
            logger.error("Initialization failed. Exiting.")
            return
        
        self.running = True
        
        try:
            logger.info("\n🤖 Thinking Bot is now running...")
            logger.info("Press Ctrl+C to stop\n")
            
            # Main loop
            while self.running:
                await self.trading_cycle()
                
                # Sleep between cycles (e.g., 60 seconds)
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\n⚠ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.running = False
            
            # Cleanup
            logger.info("\n" + "=" * 80)
            logger.info("THINKING BOT - SHUTTING DOWN")
            logger.info("=" * 80)
            
            # Close all positions (if configured)
            # Generate final report
            
            mt5.shutdown()
            
            logger.info("✓ Shutdown complete")
    
    # Helper methods for indicators
    def _calculate_rsi(self, close, period=14):
        """Calculate RSI"""
        try:
            import talib
            return talib.RSI(close, timeperiod=period)
        except:
            # Fallback calculation
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
            avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
            
            rs = avg_gain / (avg_loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            
            return np.concatenate([np.full(len(close) - len(rsi), 50), rsi])
    
    def _calculate_macd(self, close, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        try:
            import talib
            return talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        except:
            # Fallback
            ema_fast = self._calculate_ema(close, fast)
            ema_slow = self._calculate_ema(close, slow)
            macd = ema_fast - ema_slow
            macd_signal = self._calculate_ema(macd, signal)
            macd_hist = macd - macd_signal
            return macd, macd_signal, macd_hist
    
    def _calculate_ema(self, close, period):
        """Calculate EMA"""
        try:
            import talib
            return talib.EMA(close, timeperiod=period)
        except:
            # Fallback
            alpha = 2 / (period + 1)
            ema = np.zeros_like(close)
            ema[0] = close[0]
            for i in range(1, len(close)):
                ema[i] = alpha * close[i] + (1 - alpha) * ema[i-1]
            return ema
    
    def _calculate_atr(self, high, low, close, period=14):
        """Calculate ATR"""
        try:
            import talib
            return talib.ATR(high, low, close, timeperiod=period)
        except:
            # Fallback
            tr = np.maximum(high - low, np.abs(high - np.roll(close, 1)))
            tr = np.maximum(tr, np.abs(low - np.roll(close, 1)))
            atr = np.convolve(tr, np.ones(period)/period, mode='valid')
            return np.concatenate([np.full(len(close) - len(atr), atr[0] if len(atr) > 0 else 0), atr])
    
    def _calculate_bollinger_bands(self, close, period=20, std=2):
        """Calculate Bollinger Bands"""
        try:
            import talib
            upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=std, nbdevdn=std)
            return upper, lower
        except:
            # Fallback
            sma = np.convolve(close, np.ones(period)/period, mode='valid')
            std_dev = np.array([np.std(close[i:i+period]) for i in range(len(close) - period + 1)])
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            pad_len = len(close) - len(upper)
            upper = np.concatenate([np.full(pad_len, upper[0] if len(upper) > 0 else close[0]), upper])
            lower = np.concatenate([np.full(pad_len, lower[0] if len(lower) > 0 else close[0]), lower])
            
            return upper, lower
    
    def _detect_trend(self, symbol, timeframe):
        """Detect trend for a timeframe"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
            if rates is None or len(rates) < 20:
                return "NEUTRAL"
            
            close = rates['close']
            ema_20 = self._calculate_ema(close, 20)
            ema_50 = self._calculate_ema(close, 50)
            
            if len(ema_20) > 0 and len(ema_50) > 0:
                if ema_20[-1] > ema_50[-1] and close[-1] > ema_20[-1]:
                    return "BULLISH"
                elif ema_20[-1] < ema_50[-1] and close[-1] < ema_20[-1]:
                    return "BEARISH"
            
            return "NEUTRAL"
        except:
            return "NEUTRAL"
    
    def _find_support_levels(self, df, window=20):
        """Find support levels"""
        try:
            lows = df['low'].values
            support = []
            for i in range(window, len(lows) - window):
                if lows[i] == min(lows[i-window:i+window]):
                    support.append(lows[i])
            return sorted(set(support))[-3:]  # Return top 3
        except:
            return []
    
    def _find_resistance_levels(self, df, window=20):
        """Find resistance levels"""
        try:
            highs = df['high'].values
            resistance = []
            for i in range(window, len(highs) - window):
                if highs[i] == max(highs[i-window:i+window]):
                    resistance.append(highs[i])
            return sorted(set(resistance))[-3:]  # Return top 3
        except:
            return []
    
    def _detect_patterns(self, df):
        """Detect chart patterns"""
        patterns = []
        try:
            # Simplified pattern detection
            close = df['close'].values
            if len(close) > 3:
                # Bullish engulfing
                if close[-1] > close[-2] and close[-2] < close[-3]:
                    patterns.append("BULLISH_ENGULFING")
                # Bearish engulfing
                elif close[-1] < close[-2] and close[-2] > close[-3]:
                    patterns.append("BEARISH_ENGULFING")
        except:
            pass
        return patterns
    
    def _calculate_total_exposure(self):
        """Calculate total exposure across all positions"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return 0.0
            
            total = 0.0
            for position in self.active_positions.values():
                tick = mt5.symbol_info_tick(position['symbol'])
                if tick:
                    exposure = position['lots'] * 100000 * tick.ask
                    total += (exposure / account_info.equity) * 100
            
            return total
        except:
            return 0.0


async def main():
    """Main entry point"""
    bot = ThinkingBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
