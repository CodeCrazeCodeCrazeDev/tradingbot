"""
Ultimate Production Engine - The Heart of the Trading System
============================================================

This is the master orchestrator that coordinates all trading operations.
It integrates:
- Multi-strategy ensemble with dynamic weighting
- Real-time ML predictions with confidence calibration
- Institutional-grade risk management
- Smart order execution with market impact optimization
- Self-learning and continuous improvement
- Comprehensive monitoring and alerting

Design Principles:
1. SURVIVAL FIRST - Never risk more than we can afford to lose
2. EDGE PRESERVATION - Only trade when we have statistical edge
3. EXECUTION EXCELLENCE - Minimize slippage and market impact
4. CONTINUOUS LEARNING - Improve from every trade
5. FULL TRANSPARENCY - Log everything, explain every decision
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from pathlib import Path
import numpy as np
import pandas as pd
import threading
import traceback
import hashlib
import uuid

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """Trading execution modes"""
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"
    SHADOW = "shadow"  # Run alongside but don't execute


class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    TRADING = "trading"
    PAUSED = "paused"
    EMERGENCY_STOP = "emergency_stop"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class SignalStrength(Enum):
    """Signal strength classification"""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1
    NEUTRAL = 0


@dataclass
class MarketCondition:
    """Current market condition assessment"""
    timestamp: datetime
    regime: str  # trending_up, trending_down, ranging, volatile, quiet
    volatility: float  # 0-1 normalized
    liquidity: float  # 0-1 normalized
    trend_strength: float  # -1 to 1
    momentum: float  # -1 to 1
    fear_greed_index: float  # 0-100
    correlation_regime: str  # normal, decorrelated, highly_correlated
    news_sentiment: float  # -1 to 1
    is_tradeable: bool
    reason: str = ""


@dataclass
class TradingSignal:
    """Unified trading signal from all sources"""
    signal_id: str
    timestamp: datetime
    symbol: str
    direction: str  # BUY, SELL, HOLD
    strength: SignalStrength
    confidence: float  # 0-1
    expected_return: float
    expected_risk: float
    risk_reward_ratio: float
    sources: List[str]  # Which strategies/models generated this
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    max_holding_period: timedelta
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction,
            'strength': self.strength.name,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'expected_risk': self.expected_risk,
            'risk_reward_ratio': self.risk_reward_ratio,
            'sources': self.sources,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'max_holding_period': str(self.max_holding_period),
            'metadata': self.metadata,
        }


@dataclass
class TradeExecution:
    """Record of an executed trade"""
    execution_id: str
    signal_id: str
    timestamp: datetime
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: float = 0.0
    take_profit: float = 0.0
    status: str = "open"  # open, closed, stopped_out, take_profit_hit
    pnl: float = 0.0
    pnl_percent: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    holding_time: Optional[timedelta] = None
    exit_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance tracking"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    avg_holding_time: timedelta = field(default_factory=lambda: timedelta(0))
    expectancy: float = 0.0
    kelly_fraction: float = 0.0
    
    def update_from_trade(self, trade: TradeExecution):
        """Update metrics from a closed trade"""
        if trade.status != "closed" and trade.status != "stopped_out" and trade.status != "take_profit_hit":
            return
            
        self.total_trades += 1
        self.realized_pnl += trade.pnl
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        
        if trade.pnl > 0:
            self.winning_trades += 1
            self.gross_profit += trade.pnl
            self.largest_win = max(self.largest_win, trade.pnl)
        else:
            self.losing_trades += 1
            self.gross_loss += abs(trade.pnl)
            self.largest_loss = max(self.largest_loss, abs(trade.pnl))
        
        # Update ratios
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
            
        if self.winning_trades > 0:
            self.avg_win = self.gross_profit / self.winning_trades
            
        if self.losing_trades > 0:
            self.avg_loss = self.gross_loss / self.losing_trades
            
        if self.gross_loss > 0:
            self.profit_factor = self.gross_profit / self.gross_loss
            
        # Expectancy
        if self.total_trades > 0:
            self.expectancy = (self.win_rate * self.avg_win) - ((1 - self.win_rate) * self.avg_loss)
            
        # Kelly fraction
        if self.avg_loss > 0 and self.profit_factor > 0:
            self.kelly_fraction = self.win_rate - ((1 - self.win_rate) / (self.avg_win / self.avg_loss if self.avg_loss > 0 else 1))
            self.kelly_fraction = max(0, min(0.25, self.kelly_fraction))  # Cap at 25%


class UltimateProductionEngine:
    """
    The Ultimate Production Trading Engine
    
    This is the master orchestrator that coordinates all trading operations.
    It's designed to be:
    - Robust: Handles errors gracefully, never crashes
    - Transparent: Logs everything, explains every decision
    - Adaptive: Learns and improves from every trade
    - Safe: Multiple layers of risk protection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Ultimate Production Engine"""
        self.config = config or {}
        self.engine_id = str(uuid.uuid4())[:8]
        
        # Core state
        self.state = SystemState.INITIALIZING
        self.mode = TradingMode(self.config.get('mode', 'paper'))
        self.start_time: Optional[datetime] = None
        self.last_heartbeat: datetime = datetime.now()
        
        # Trading state
        self.symbols = self.config.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
        self.capital = self.config.get('initial_capital', 10000.0)
        self.available_capital = self.capital
        self.positions: Dict[str, TradeExecution] = {}
        self.pending_signals: List[TradingSignal] = []
        self.trade_history: List[TradeExecution] = []
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.daily_pnl: Dict[str, float] = {}
        
        # Risk limits
        self.max_daily_loss = self.config.get('max_daily_loss', 0.02)  # 2%
        self.max_drawdown = self.config.get('max_drawdown', 0.10)  # 10%
        self.max_position_size = self.config.get('max_position_size', 0.02)  # 2% per position
        self.max_positions = self.config.get('max_positions', 5)
        self.max_correlation = self.config.get('max_correlation', 0.7)
        
        # Components (initialized lazily)
        self._strategy_ensemble = None
        self._ml_engine = None
        self._risk_fortress = None
        self._smart_executor = None
        self._live_monitor = None
        self._self_learner = None
        
        # Event handlers
        self._on_signal_callbacks: List[Callable] = []
        self._on_trade_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []
        
        # Threading
        self._lock = threading.RLock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Data storage
        self.data_dir = Path(self.config.get('data_dir', 'ultimate_production_data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"UltimateProductionEngine initialized [ID: {self.engine_id}] [Mode: {self.mode.value}]")
    
    @property
    def strategy_ensemble(self):
        """Lazy load strategy ensemble"""
        if self._strategy_ensemble is None:
            from .strategy_ensemble import StrategyEnsemble
            self._strategy_ensemble = StrategyEnsemble(self.config.get('strategy_config', {}))
        return self._strategy_ensemble
    
    @property
    def ml_engine(self):
        """Lazy load ML prediction engine"""
        if self._ml_engine is None:
            from .ml_prediction_engine import MLPredictionEngine
            self._ml_engine = MLPredictionEngine(self.config.get('ml_config', {}))
        return self._ml_engine
    
    @property
    def risk_fortress(self):
        """Lazy load risk management"""
        if self._risk_fortress is None:
            from .risk_fortress import RiskFortress
            self._risk_fortress = RiskFortress(self.config.get('risk_config', {}))
        return self._risk_fortress
    
    @property
    def smart_executor(self):
        """Lazy load smart executor"""
        if self._smart_executor is None:
            from .smart_executor import SmartExecutor
            self._smart_executor = SmartExecutor(self.config.get('execution_config', {}))
        return self._smart_executor
    
    @property
    def live_monitor(self):
        """Lazy load live monitor"""
        if self._live_monitor is None:
            from .live_monitor import LiveMonitor
            self._live_monitor = LiveMonitor(self.config.get('monitor_config', {}))
        return self._live_monitor
    
    @property
    def self_learner(self):
        """Lazy load self learner"""
        if self._self_learner is None:
            from .self_learner import SelfLearner
            self._self_learner = SelfLearner(self.config.get('learning_config', {}))
        return self._self_learner
    
    async def initialize(self) -> bool:
        """Initialize all components and prepare for trading"""
        try:
            logger.info("Initializing Ultimate Production Engine...")
            
            # Initialize components
            await self._initialize_components()
            
            # Load historical state
            await self._load_state()
            
            # Validate configuration
            self._validate_config()
            
            # Run pre-flight checks
            passed, issues = await self._preflight_checks()
            if not passed:
                logger.error(f"Pre-flight checks failed: {issues}")
                self.state = SystemState.ERROR
                return False
            
            self.state = SystemState.READY
            logger.info("Ultimate Production Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}\n{traceback.format_exc()}")
            self.state = SystemState.ERROR
            return False
    
    async def _initialize_components(self):
        """Initialize all trading components"""
        logger.info("Initializing trading components...")
        
        try:
            # Initialize each component
            _ = self.strategy_ensemble
            logger.info("Strategy ensemble initialized")
        except Exception as e:
            logger.warning(f"Strategy ensemble initialization warning: {e}")
            _ = self.ml_engine
            logger.info("ML prediction engine initialized")
        except Exception as e:
            logger.warning(f"ML engine initialization warning: {e}")
        
            _ = self.risk_fortress
            logger.info("Risk fortress initialized")
        except Exception as e:
            logger.warning(f"Risk fortress initialization warning: {e}")
        
            _ = self.smart_executor
            logger.info("Smart executor initialized")
        except Exception as e:
            logger.warning(f"Smart executor initialization warning: {e}")
        
            _ = self.live_monitor
            logger.info("Live monitor initialized")
        except Exception as e:
            logger.warning(f"Live monitor initialization warning: {e}")
        
            _ = self.self_learner
            logger.info("Self learner initialized")
        except Exception as e:
            logger.warning(f"Self learner initialization warning: {e}")
    
    async def _load_state(self):
        """Load previous state from disk"""
        state_file = self.data_dir / 'engine_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.capital = state.get('capital', self.capital)
                    self.available_capital = state.get('available_capital', self.available_capital)
                    logger.info(f"Loaded previous state: capital=${self.capital:.2f}")
            except Exception as e:
                logger.warning(f"Could not load previous state: {e}")
    
    async def _save_state(self):
        """Save current state to disk"""
        state_file = self.data_dir / 'engine_state.json'
        try:
            state = {
                'capital': self.capital,
                'available_capital': self.available_capital,
                'last_save': datetime.now().isoformat(),
                'total_trades': self.metrics.total_trades,
                'total_pnl': self.metrics.total_pnl,
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def _validate_config(self):
        """Validate configuration parameters"""
        assert self.capital > 0, "Capital must be positive"
        assert 0 < self.max_daily_loss <= 0.1, "Max daily loss must be between 0 and 10%"
        assert 0 < self.max_drawdown <= 0.3, "Max drawdown must be between 0 and 30%"
        assert 0 < self.max_position_size <= 0.1, "Max position size must be between 0 and 10%"
        assert self.max_positions >= 1, "Must allow at least 1 position"
        logger.info("Configuration validated")
    
    async def _preflight_checks(self) -> Tuple[bool, List[str]]:
        """Run pre-flight checks before trading"""
        issues = []
        
        # Check capital
        if self.capital <= 0:
            issues.append("No capital available")
        
        # Check symbols
        if not self.symbols:
            issues.append("No symbols configured")
        
        # Check daily loss limit
        today = datetime.now().strftime('%Y-%m-%d')
        daily_loss = self.daily_pnl.get(today, 0)
        if daily_loss < -self.max_daily_loss * self.capital:
            issues.append(f"Daily loss limit reached: ${daily_loss:.2f}")
        
        # Check drawdown
        if self.metrics.current_drawdown > self.max_drawdown:
            issues.append(f"Max drawdown exceeded: {self.metrics.current_drawdown:.2%}")
        
        return len(issues) == 0, issues
    
    async def start(self):
        """Start the trading engine"""
        if self.state != SystemState.READY:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize engine")
        
        logger.info("Starting Ultimate Production Engine...")
        self.state = SystemState.TRADING
        self.start_time = datetime.now()
        self._running = True
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._main_trading_loop()),
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._learning_loop()),
            asyncio.create_task(self._heartbeat_loop()),
        ]
        
        logger.info(f"Trading engine started in {self.mode.value} mode")
    
    async def stop(self):
        """Stop the trading engine gracefully"""
        logger.info("Stopping Ultimate Production Engine...")
        self.state = SystemState.SHUTTING_DOWN
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Close all positions if in live mode
        if self.mode == TradingMode.LIVE:
            await self._close_all_positions("System shutdown")
        
        # Save state
        await self._save_state()
        
        self.state = SystemState.READY
        logger.info("Trading engine stopped")
    
    async def _main_trading_loop(self):
        """Main trading loop - the heart of the system"""
        logger.info("Main trading loop started")
        
        while self._running:
            try:
                # Check if we should be trading
                if self.state != SystemState.TRADING:
                    await asyncio.sleep(1)
                    continue
                
                # 1. Get market data
                market_data = await self._get_market_data()
                
                # 2. Assess market conditions
                market_condition = await self._assess_market_condition(market_data)
                
                # 3. Check if market is tradeable
                if not market_condition.is_tradeable:
                    logger.debug(f"Market not tradeable: {market_condition.reason}")
                    await asyncio.sleep(1)
                    continue
                
                # 4. Generate signals from all sources
                signals = await self._generate_signals(market_data, market_condition)
                
                # 5. Filter and validate signals
                valid_signals = await self._validate_signals(signals, market_condition)
                
                # 6. Risk check each signal
                approved_signals = await self._risk_check_signals(valid_signals)
                
                # 7. Execute approved signals
                for signal in approved_signals:
                    await self._execute_signal(signal)
                
                # 8. Manage existing positions
                await self._manage_positions(market_data)
                
                # 9. Update metrics
                self._update_metrics()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main trading loop: {e}\n{traceback.format_exc()}")
                await self._handle_error(e)
                await asyncio.sleep(5)
        
        logger.info("Main trading loop stopped")
    
    async def _get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Get current market data for all symbols"""
        market_data = {}
        
        for symbol in self.symbols:
            try:
                # Try to get real data from data sources
                data = await self._fetch_symbol_data(symbol)
                if data is not None and not data.empty:
                    market_data[symbol] = data
                else:
                    # Generate synthetic data for paper trading
                    market_data[symbol] = self._generate_synthetic_data(symbol)
            except Exception as e:
                logger.warning(f"Could not get data for {symbol}: {e}")
                market_data[symbol] = self._generate_synthetic_data(symbol)
        
        return market_data
    
    async def _fetch_symbol_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch real market data for a symbol"""
        try:
            # Try multiple data sources
            # Try MT5 first
            from trading_bot.data.mt5_interface import MT5Interface
            mt5 = MT5Interface()
            data = mt5.get_rates(symbol, 'M1', 100)
            if data is not None and len(data) > 0:
                return data
        except Exception:
            pass

        try:
            # Try Yahoo Finance
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            if data is not None and len(data) > 0:
                return data
        except Exception:
            pass
        
        return None
    
    def _generate_synthetic_data(self, symbol: str) -> pd.DataFrame:
        """Generate synthetic market data for paper trading"""
        # Base prices for common symbols
        base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'AUDUSD': 0.6550,
            'USDCAD': 1.3550,
            'BTCUSD': 42000.0,
            'ETHUSD': 2500.0,
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Generate 100 bars of synthetic data
        np.random.seed(int(datetime.now().timestamp()) % 10000)
        
        returns = np.random.normal(0, 0.0002, 100)  # Small random returns
        prices = base_price * np.cumprod(1 + returns)
        
        # Add some trend
        trend = np.linspace(0, np.random.uniform(-0.002, 0.002), 100)
        prices = prices * (1 + trend)
        
        # Create OHLCV data
        data = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.0001, 0.0001, 100)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0003, 100))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0003, 100))),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100),
        })
        
        # Ensure high >= open, close and low <= open, close
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        # Add timestamp index
        data.index = pd.date_range(end=datetime.now(), periods=100, freq='1min')
        
        return data
    
    async def _assess_market_condition(self, market_data: Dict[str, pd.DataFrame]) -> MarketCondition:
        """Assess current market conditions"""
        try:
            # Aggregate analysis across all symbols
            volatilities = []
            trends = []
            momentums = []
            
            for symbol, data in market_data.items():
                if data is None or data.empty:
                    continue
                
                # Calculate volatility (ATR-based)
                if len(data) >= 14:
                    high_low = data['high'] - data['low']
                    high_close = np.abs(data['high'] - data['close'].shift())
                    low_close = np.abs(data['low'] - data['close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean().iloc[-1]
                    volatility = atr / data['close'].iloc[-1]
                    volatilities.append(volatility)
                
                # Calculate trend (SMA-based)
                if len(data) >= 20:
                    sma20 = data['close'].rolling(20).mean().iloc[-1]
                    sma50 = data['close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else sma20
                    current_price = data['close'].iloc[-1]
                    trend = (current_price - sma20) / sma20
                    trends.append(trend)
                
                # Calculate momentum (RSI-based)
                if len(data) >= 14:
                    delta = data['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss.replace(0, 1e-10)
                    rsi = 100 - (100 / (1 + rs))
                    momentum = (rsi.iloc[-1] - 50) / 50  # Normalize to -1 to 1
                    momentums.append(momentum)
            
            # Aggregate
            avg_volatility = np.mean(volatilities) if volatilities else 0.5
            avg_trend = np.mean(trends) if trends else 0
            avg_momentum = np.mean(momentums) if momentums else 0
            
            # Determine regime
            if avg_volatility > 0.02:
                regime = "volatile"
            elif abs(avg_trend) > 0.01:
                regime = "trending_up" if avg_trend > 0 else "trending_down"
            elif avg_volatility < 0.005:
                regime = "quiet"
            else:
                regime = "ranging"
            
            # Determine if tradeable
            is_tradeable = True
            reason = ""
            
            # Don't trade in extreme volatility
            if avg_volatility > 0.05:
                is_tradeable = False
                reason = "Extreme volatility"
            
            # Check daily loss limit
            today = datetime.now().strftime('%Y-%m-%d')
            daily_loss = self.daily_pnl.get(today, 0)
            if daily_loss < -self.max_daily_loss * self.capital:
                is_tradeable = False
                reason = "Daily loss limit reached"
            
            return MarketCondition(
                timestamp=datetime.now(),
                regime=regime,
                volatility=min(1.0, avg_volatility * 50),  # Normalize to 0-1
                liquidity=0.8,  # Assume good liquidity for now
                trend_strength=avg_trend,
                momentum=avg_momentum,
                fear_greed_index=50 + avg_momentum * 30,  # Simple approximation
                correlation_regime="normal",
                news_sentiment=0,
                is_tradeable=is_tradeable,
                reason=reason,
            )
            
        except Exception as e:
            logger.error(f"Error assessing market condition: {e}")
            return MarketCondition(
                timestamp=datetime.now(),
                regime="unknown",
                volatility=0.5,
                liquidity=0.5,
                trend_strength=0,
                momentum=0,
                fear_greed_index=50,
                correlation_regime="unknown",
                news_sentiment=0,
                is_tradeable=False,
                reason=f"Error: {e}",
            )
    
    async def _generate_signals(
        self, 
        market_data: Dict[str, pd.DataFrame],
        market_condition: MarketCondition
    ) -> List[TradingSignal]:
        """Generate trading signals from all sources"""
        all_signals = []
        
        # 1. Strategy ensemble signals
        try:
            strategy_signals = await self.strategy_ensemble.generate_signals(
                market_data, market_condition
            )
            all_signals.extend(strategy_signals)
        except Exception as e:
            logger.warning(f"Strategy ensemble error: {e}")
        # 2. ML prediction signals
            ml_signals = await self.ml_engine.generate_signals(
                market_data, market_condition
            )
            all_signals.extend(ml_signals)
        except Exception as e:
            logger.warning(f"ML engine error: {e}")
        
        # 3. Combine and deduplicate signals
        combined_signals = self._combine_signals(all_signals)
        
        return combined_signals
    
    def _combine_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Combine signals from multiple sources"""
        if not signals:
            return []
        
        # Group by symbol
        symbol_signals: Dict[str, List[TradingSignal]] = {}
        for signal in signals:
            if signal.symbol not in symbol_signals:
                symbol_signals[signal.symbol] = []
            symbol_signals[signal.symbol].append(signal)
        
        combined = []
        for symbol, sym_signals in symbol_signals.items():
            if len(sym_signals) == 1:
                combined.append(sym_signals[0])
                continue
            
            # Combine multiple signals for same symbol
            # Weight by confidence
            total_confidence = sum(s.confidence for s in sym_signals)
            if total_confidence == 0:
                continue
            
            # Weighted direction
            buy_weight = sum(s.confidence for s in sym_signals if s.direction == "BUY")
            sell_weight = sum(s.confidence for s in sym_signals if s.direction == "SELL")
            
            if buy_weight > sell_weight * 1.2:  # Need 20% more weight to trigger
                direction = "BUY"
                confidence = buy_weight / total_confidence
            elif sell_weight > buy_weight * 1.2:
                direction = "SELL"
                confidence = sell_weight / total_confidence
            else:
                continue  # Conflicting signals, skip
            
            # Use the highest confidence signal as base
            base_signal = max(sym_signals, key=lambda s: s.confidence)
            
            combined_signal = TradingSignal(
                signal_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                symbol=symbol,
                direction=direction,
                strength=base_signal.strength,
                confidence=confidence,
                expected_return=base_signal.expected_return,
                expected_risk=base_signal.expected_risk,
                risk_reward_ratio=base_signal.risk_reward_ratio,
                sources=[s.sources[0] if s.sources else "unknown" for s in sym_signals],
                entry_price=base_signal.entry_price,
                stop_loss=base_signal.stop_loss,
                take_profit=base_signal.take_profit,
                position_size=base_signal.position_size,
                max_holding_period=base_signal.max_holding_period,
                metadata={'combined_from': len(sym_signals)},
            )
            combined.append(combined_signal)
        
        return combined
    
    async def _validate_signals(
        self,
        signals: List[TradingSignal],
        market_condition: MarketCondition
    ) -> List[TradingSignal]:
        """Validate and filter signals"""
        valid_signals = []
        
        for signal in signals:
            # Check minimum confidence
            if signal.confidence < 0.6:
                logger.debug(f"Signal {signal.signal_id} rejected: low confidence {signal.confidence:.2f}")
                continue
            
            # Check risk/reward ratio
            if signal.risk_reward_ratio < 1.5:
                logger.debug(f"Signal {signal.signal_id} rejected: poor R:R {signal.risk_reward_ratio:.2f}")
                continue
            
            # Check if we already have a position in this symbol
            if signal.symbol in self.positions:
                logger.debug(f"Signal {signal.signal_id} rejected: already have position in {signal.symbol}")
                continue
            
            # Check max positions
            if len(self.positions) >= self.max_positions:
                logger.debug(f"Signal {signal.signal_id} rejected: max positions reached")
                continue
            
            # Check market regime compatibility
            if market_condition.regime == "volatile" and signal.strength.value < 4:
                logger.debug(f"Signal {signal.signal_id} rejected: weak signal in volatile market")
                continue
            
            valid_signals.append(signal)
        
        return valid_signals
    
    async def _risk_check_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Apply risk management checks to signals"""
        approved = []
        
        for signal in signals:
            try:
                # Check with risk fortress
                is_approved, adjusted_signal = await self.risk_fortress.check_signal(
                    signal, 
                    self.capital,
                    self.available_capital,
                    self.positions,
                    self.metrics
                )
                
                if is_approved:
                    approved.append(adjusted_signal)
                else:
                    logger.info(f"Signal {signal.signal_id} rejected by risk fortress")
                    
            except Exception as e:
                logger.warning(f"Risk check error for signal {signal.signal_id}: {e}")
                # Be conservative - reject on error
                continue
        
        return approved
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute a trading signal"""
        try:
            logger.info(f"Executing signal: {signal.direction} {signal.symbol} @ {signal.entry_price:.5f}")
            
            # Create trade execution record
            execution = TradeExecution(
                execution_id=str(uuid.uuid4())[:8],
                signal_id=signal.signal_id,
                timestamp=datetime.now(),
                symbol=signal.symbol,
                direction=signal.direction,
                quantity=signal.position_size,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                status="open",
                metadata=signal.metadata,
            )
            
            # Execute through smart executor
            if self.mode == TradingMode.LIVE:
                result = await self.smart_executor.execute(execution)
                if not result.success:
                    logger.error(f"Execution failed: {result.error}")
                    return
                execution.entry_price = result.fill_price
                execution.fees = result.fees
                execution.slippage = result.slippage
            
            # Record position
            with self._lock:
                self.positions[signal.symbol] = execution
                self.available_capital -= execution.quantity * execution.entry_price
            
            # Notify callbacks
            for callback in self._on_trade_callbacks:
                try:
                    callback(execution)
                except Exception as e:
                    logger.error(f"Trade callback error: {e}")
            
            logger.info(f"Trade opened: {execution.execution_id} {execution.direction} {execution.symbol}")
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}\n{traceback.format_exc()}")
    
    async def _manage_positions(self, market_data: Dict[str, pd.DataFrame]):
        """Manage existing positions - check stops, targets, etc."""
        positions_to_close = []
        
        with self._lock:
            for symbol, position in self.positions.items():
                if symbol not in market_data:
                    continue
                
                data = market_data[symbol]
                if data.empty:
                    continue
                
                current_price = data['close'].iloc[-1]
                
                # Update position P&L
                if position.direction == "BUY":
                    position.pnl = (current_price - position.entry_price) * position.quantity
                    position.pnl_percent = (current_price - position.entry_price) / position.entry_price
                    
                    # Check stop loss
                    if current_price <= position.stop_loss:
                        position.exit_price = position.stop_loss
                        position.exit_reason = "stop_loss"
                        position.status = "stopped_out"
                        positions_to_close.append(symbol)
                    
                    # Check take profit
                    elif current_price >= position.take_profit:
                        position.exit_price = position.take_profit
                        position.exit_reason = "take_profit"
                        position.status = "take_profit_hit"
                        positions_to_close.append(symbol)
                
                else:  # SELL
                    position.pnl = (position.entry_price - current_price) * position.quantity
                    position.pnl_percent = (position.entry_price - current_price) / position.entry_price
                    
                    # Check stop loss
                    if current_price >= position.stop_loss:
                        position.exit_price = position.stop_loss
                        position.exit_reason = "stop_loss"
                        position.status = "stopped_out"
                        positions_to_close.append(symbol)
                    
                    # Check take profit
                    elif current_price <= position.take_profit:
                        position.exit_price = position.take_profit
                        position.exit_reason = "take_profit"
                        position.status = "take_profit_hit"
                        positions_to_close.append(symbol)
        
        # Close positions
        for symbol in positions_to_close:
            await self._close_position(symbol)
    
    async def _close_position(self, symbol: str, reason: str = ""):
        """Close a position"""
        with self._lock:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            
            if not position.exit_price:
                # Get current price
                data = await self._fetch_symbol_data(symbol)
                if data is not None and not data.empty:
                    position.exit_price = data['close'].iloc[-1]
                else:
                    position.exit_price = position.entry_price  # Fallback
            
            # Calculate final P&L
            if position.direction == "BUY":
                position.pnl = (position.exit_price - position.entry_price) * position.quantity
            else:
                position.pnl = (position.entry_price - position.exit_price) * position.quantity
            
            position.pnl -= position.fees
            position.holding_time = datetime.now() - position.timestamp
            position.status = "closed" if not position.status.startswith("stopped") else position.status
            if reason:
                position.exit_reason = reason
            
            # Update capital
            self.available_capital += position.quantity * position.entry_price + position.pnl
            self.capital += position.pnl
            
            # Update daily P&L
            today = datetime.now().strftime('%Y-%m-%d')
            self.daily_pnl[today] = self.daily_pnl.get(today, 0) + position.pnl
            
            # Move to history
            self.trade_history.append(position)
            del self.positions[symbol]
            
            # Update metrics
            self.metrics.update_from_trade(position)
            
            # Record equity
            self.equity_curve.append((datetime.now(), self.capital))
            
            try:
                # Learn from trade
                await self.self_learner.learn_from_trade(position)
            except Exception as e:
                logger.warning(f"Learning error: {e}")
            
            logger.info(
                f"Position closed: {position.symbol} {position.direction} "
                f"P&L: ${position.pnl:.2f} ({position.pnl_percent:.2%}) "
                f"Reason: {position.exit_reason}"
            )
    
    async def _close_all_positions(self, reason: str = ""):
        """Close all open positions"""
        symbols = list(self.positions.keys())
        for symbol in symbols:
            await self._close_position(symbol, reason)
    
    def _update_metrics(self):
        """Update performance metrics"""
        # Update unrealized P&L
        unrealized = sum(p.pnl for p in self.positions.values())
        self.metrics.unrealized_pnl = unrealized
        self.metrics.total_pnl = self.metrics.realized_pnl + unrealized
        
        # Update drawdown
        if self.equity_curve:
            peak = max(eq[1] for eq in self.equity_curve)
            current = self.capital
            self.metrics.current_drawdown = (peak - current) / peak if peak > 0 else 0
            self.metrics.max_drawdown = max(self.metrics.max_drawdown, self.metrics.current_drawdown)
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # Update live monitor
                await self.live_monitor.update(
                    state=self.state,
                    capital=self.capital,
                    positions=self.positions,
                    metrics=self.metrics,
                )
                
                # Check for alerts
                alerts = await self.live_monitor.check_alerts()
                for alert in alerts:
                    logger.warning(f"ALERT: {alert}")
                
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _learning_loop(self):
        """Background learning loop"""
        while self._running:
            try:
                # Periodic learning updates
                await self.self_learner.update()
                await asyncio.sleep(60)  # Learn every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Learning error: {e}")
                await asyncio.sleep(60)
    
    async def _heartbeat_loop(self):
        """Heartbeat loop for health monitoring"""
        while self._running:
            try:
                self.last_heartbeat = datetime.now()
                
                # Save state periodically
                await self._save_state()
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(30)
    
    async def _handle_error(self, error: Exception):
        """Handle errors gracefully"""
        for callback in self._on_error_callbacks:
            try:
                callback(error)
            except Exception:
                pass
        
        # Check if we should pause trading
        error_count = sum(1 for t in self.trade_history[-10:] if t.exit_reason == "error")
        if error_count >= 3:
            logger.warning("Too many errors, pausing trading")
            self.state = SystemState.PAUSED
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'engine_id': self.engine_id,
            'state': self.state.value,
            'mode': self.mode.value,
            'uptime': str(datetime.now() - self.start_time) if self.start_time else "0",
            'capital': self.capital,
            'available_capital': self.available_capital,
            'open_positions': len(self.positions),
            'total_trades': self.metrics.total_trades,
            'win_rate': f"{self.metrics.win_rate:.2%}",
            'total_pnl': f"${self.metrics.total_pnl:.2f}",
            'max_drawdown': f"{self.metrics.max_drawdown:.2%}",
            'last_heartbeat': self.last_heartbeat.isoformat(),
        }
    
    def on_signal(self, callback: Callable):
        """Register callback for new signals"""
        self._on_signal_callbacks.append(callback)
    
    def on_trade(self, callback: Callable):
        """Register callback for trade executions"""
        self._on_trade_callbacks.append(callback)
    
    def on_error(self, callback: Callable):
        """Register callback for errors"""
        self._on_error_callbacks.append(callback)


async def quick_start(config: Optional[Dict[str, Any]] = None) -> UltimateProductionEngine:
    """Quick start helper for the Ultimate Production Engine"""
    engine = UltimateProductionEngine(config)
    await engine.initialize()
    return engine
