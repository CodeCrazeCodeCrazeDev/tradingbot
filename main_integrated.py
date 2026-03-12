#!/usr/bin/env python3
"""
AlphaAlgo Trading Bot - Unified Main Entry Point
=================================================

This is the SINGLE entry point that integrates ALL modules from the trading_bot package.

Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED TRADING SYSTEM                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 7: ORCHESTRATION - Event Bus, Service Registry, Lifecycle    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 6: AI/ML - Predictions, RL Agents, Sentiment, Patterns       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 5: SIGNALS - Generation, Filtering, Multi-Timeframe          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 4: ANALYSIS - Market Structure, Liquidity, Order Flow        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: EXECUTION - Order Management, Smart Routing, Fills        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: RISK - Position Sizing, Drawdown, Circuit Breakers        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: DATA - MT5 Interface, Market Data, Feeds                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Layer 0: SAFETY (IMMUTABLE) - Kill Switch, Fail-Safe, Limits       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

Usage:
    python main_integrated.py --mode paper --symbol EURUSD
    python main_integrated.py --mode live --symbol BTCUSD --use-ml
    python main_integrated.py --help

Author: AlphaAlgo Team
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['GYM_IGNORE_DEPRECATION_WARNING'] = '1'

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AlphaAlgo')

# Ensure directories exist
Path('logs').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)
Path('models').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)

# =============================================================================
# MODULE AVAILABILITY TRACKING
# =============================================================================

_AVAILABLE: Dict[str, bool] = {}

def safe_import(module_path: str, names: List[str], category: str) -> Dict[str, Any]:
    """Safely import modules with graceful degradation."""
    result = {}
    try:
        module = __import__(module_path, fromlist=names)
        for name in names:
            if hasattr(module, name):
                result[name] = getattr(module, name)
                _AVAILABLE[f"{category}.{name}"] = True
            else:
                _AVAILABLE[f"{category}.{name}"] = False
    except ImportError as e:
        logger.debug(f"Optional module {module_path} not available: {e}")
        for name in names:
            _AVAILABLE[f"{category}.{name}"] = False
    except Exception as e:
        logger.warning(f"Error importing {module_path}: {e}")
        for name in names:
            _AVAILABLE[f"{category}.{name}"] = False
    return result


# =============================================================================
# LAYER 0: SAFETY (IMMUTABLE) - Always loaded first
# =============================================================================

logger.info("Loading Layer 0: Safety Systems...")

# Emergency Kill Switch
try:
    from trading_bot.core.emergency_kill_switch import EmergencyKillSwitch
    _AVAILABLE['safety.kill_switch'] = True
except ImportError:
    EmergencyKillSwitch = None
    _AVAILABLE['safety.kill_switch'] = False

# Fail-Safe System
try:
    from trading_bot.core.fail_safe import FailSafeSystem
    _AVAILABLE['safety.fail_safe'] = True
except ImportError:
    FailSafeSystem = None
    _AVAILABLE['safety.fail_safe'] = False

# Circuit Breaker
try:
    from trading_bot.risk.circuit_breaker import CircuitBreaker
    _AVAILABLE['safety.circuit_breaker'] = True
except ImportError:
    CircuitBreaker = None
    _AVAILABLE['safety.circuit_breaker'] = False

# =============================================================================
# LAYER 1: DATA - Market Data & Connectivity
# =============================================================================

logger.info("Loading Layer 1: Data Systems...")

# MT5 Interface
try:
    from trading_bot.data.mt5_interface import MT5Interface
    _AVAILABLE['data.mt5'] = True
except ImportError:
    MT5Interface = None
    _AVAILABLE['data.mt5'] = False

# Data Manager
try:
    from trading_bot.data.data_manager import DataManager
    _AVAILABLE['data.manager'] = True
except ImportError:
    DataManager = None
    _AVAILABLE['data.manager'] = False

# Market Data Stream
try:
    from trading_bot.data.market_data_stream import MarketDataStream
    _AVAILABLE['data.stream'] = True
except ImportError:
    MarketDataStream = None
    _AVAILABLE['data.stream'] = False

# Real-time Processor
try:
    from trading_bot.data.real_time_processor import RealTimeProcessor
    _AVAILABLE['data.realtime'] = True
except ImportError:
    RealTimeProcessor = None
    _AVAILABLE['data.realtime'] = False

# =============================================================================
# LAYER 2: RISK - Risk Management & Position Sizing
# =============================================================================

logger.info("Loading Layer 2: Risk Systems...")

# Master Risk Manager
try:
    from trading_bot.risk.MASTER_risk_manager import MasterRiskManager as RiskManager
    _AVAILABLE['risk.manager'] = True
except ImportError:
    try:
        from trading_bot.risk import RiskManager
        _AVAILABLE['risk.manager'] = True
    except ImportError:
        RiskManager = None
        _AVAILABLE['risk.manager'] = False

# Drawdown Protector
try:
    from trading_bot.risk.drawdown_protector import DrawdownProtector
    _AVAILABLE['risk.drawdown'] = True
except ImportError:
    DrawdownProtector = None
    _AVAILABLE['risk.drawdown'] = False

# Pre-Trade Checks
try:
    from trading_bot.risk.pre_trade_checks import PreTradeChecker
    _AVAILABLE['risk.pre_trade'] = True
except ImportError:
    PreTradeChecker = None
    _AVAILABLE['risk.pre_trade'] = False

# Correlation Manager
try:
    from trading_bot.risk.correlation_manager import CorrelationManager
    _AVAILABLE['risk.correlation'] = True
except ImportError:
    CorrelationManager = None
    _AVAILABLE['risk.correlation'] = False

# =============================================================================
# LAYER 3: EXECUTION - Order Management & Routing
# =============================================================================

logger.info("Loading Layer 3: Execution Systems...")

# Paper Executor
try:
    from trading_bot.execution.paper_executor import PaperExecutor
    _AVAILABLE['execution.paper'] = True
except ImportError:
    PaperExecutor = None
    _AVAILABLE['execution.paper'] = False

# Live Executor
try:
    from trading_bot.execution.live_executor import LiveExecutor
    _AVAILABLE['execution.live'] = True
except ImportError:
    LiveExecutor = None
    _AVAILABLE['execution.live'] = False

# Smart Order Router
try:
    from trading_bot.execution.smart_order_router import SmartOrderRouter
    _AVAILABLE['execution.smart_router'] = True
except ImportError:
    SmartOrderRouter = None
    _AVAILABLE['execution.smart_router'] = False

# Order Manager
try:
    from trading_bot.execution.order_manager import OrderManager
    _AVAILABLE['execution.order_manager'] = True
except ImportError:
    OrderManager = None
    _AVAILABLE['execution.order_manager'] = False

# Slippage Protection
try:
    from trading_bot.execution.slippage_protection import SlippageProtector
    _AVAILABLE['execution.slippage'] = True
except ImportError:
    SlippageProtector = None
    _AVAILABLE['execution.slippage'] = False

# =============================================================================
# LAYER 4: ANALYSIS - Market Analysis & Intelligence
# =============================================================================

logger.info("Loading Layer 4: Analysis Systems...")

# Market Structure Analyzer
try:
    from trading_bot.analysis.market_structure import MarketStructureAnalyzer
    _AVAILABLE['analysis.structure'] = True
except ImportError:
    MarketStructureAnalyzer = None
    _AVAILABLE['analysis.structure'] = False

# Liquidity Analyzer
try:
    from trading_bot.analysis.liquidity import LiquidityAnalyzer
    _AVAILABLE['analysis.liquidity'] = True
except ImportError:
    LiquidityAnalyzer = None
    _AVAILABLE['analysis.liquidity'] = False

# Order Flow Analyzer
try:
    from trading_bot.analysis.order_flow import OrderFlowAnalyzer
    _AVAILABLE['analysis.order_flow'] = True
except ImportError:
    OrderFlowAnalyzer = None
    _AVAILABLE['analysis.order_flow'] = False

# Market Regime Detector
try:
    from trading_bot.analysis.market_regime_detector import MarketRegimeDetector
    _AVAILABLE['analysis.regime'] = True
except ImportError:
    MarketRegimeDetector = None
    _AVAILABLE['analysis.regime'] = False

# Sentiment Analyzer
try:
    from trading_bot.analysis.sentiment_analyzer import SentimentAnalyzer
    _AVAILABLE['analysis.sentiment'] = True
except ImportError:
    SentimentAnalyzer = None
    _AVAILABLE['analysis.sentiment'] = False

# Technical Indicators
try:
    from trading_bot.analysis.technical_indicators import TechnicalIndicators
    _AVAILABLE['analysis.technical'] = True
except ImportError:
    TechnicalIndicators = None
    _AVAILABLE['analysis.technical'] = False

# =============================================================================
# LAYER 5: SIGNALS - Signal Generation & Filtering
# =============================================================================

logger.info("Loading Layer 5: Signal Systems...")

# Strategy Engine
try:
    from trading_bot.strategy.strategy_engine import StrategyEngine, Signal
    _AVAILABLE['signals.strategy'] = True
except ImportError:
    StrategyEngine = None
    Signal = None
    _AVAILABLE['signals.strategy'] = False

# ML Strategy Engine
try:
    from trading_bot.strategy.ml_strategy_engine import MLStrategyEngine
    _AVAILABLE['signals.ml_strategy'] = True
except ImportError:
    MLStrategyEngine = None
    _AVAILABLE['signals.ml_strategy'] = False

# Signal Engine
try:
    from trading_bot.signals.signal_engine import SignalEngine
    _AVAILABLE['signals.engine'] = True
except ImportError:
    SignalEngine = None
    _AVAILABLE['signals.engine'] = False

# Multi-Timeframe Consensus
try:
    from trading_bot.signals.multi_timeframe_consensus import MultiTimeframeConsensus
    _AVAILABLE['signals.mtf'] = True
except ImportError:
    MultiTimeframeConsensus = None
    _AVAILABLE['signals.mtf'] = False

# Adaptive Thresholds
try:
    from trading_bot.signals.adaptive_thresholds import AdaptiveThresholds
    _AVAILABLE['signals.adaptive'] = True
except ImportError:
    AdaptiveThresholds = None
    _AVAILABLE['signals.adaptive'] = False

# =============================================================================
# LAYER 6: AI/ML - Machine Learning & Predictions
# =============================================================================

logger.info("Loading Layer 6: AI/ML Systems...")

# Predictive Models
try:
    from trading_bot.ml.predictive_models import PredictiveModels
    _AVAILABLE['ml.predictive'] = True
except ImportError:
    PredictiveModels = None
    _AVAILABLE['ml.predictive'] = False

# RL Agent
try:
    from trading_bot.ml.rl_agent import RLAgent
    _AVAILABLE['ml.rl_agent'] = True
except ImportError:
    RLAgent = None
    _AVAILABLE['ml.rl_agent'] = False

# Ensemble Models
try:
    from trading_bot.ml.ensemble_models import EnsembleModels
    _AVAILABLE['ml.ensemble'] = True
except ImportError:
    EnsembleModels = None
    _AVAILABLE['ml.ensemble'] = False

# Pattern Recognition
try:
    from trading_bot.ml.pattern_recognition import PatternRecognition
    _AVAILABLE['ml.patterns'] = True
except ImportError:
    PatternRecognition = None
    _AVAILABLE['ml.patterns'] = False

# Sentiment ML
try:
    from trading_bot.ml.sentiment import SentimentML
    _AVAILABLE['ml.sentiment'] = True
except ImportError:
    SentimentML = None
    _AVAILABLE['ml.sentiment'] = False

# =============================================================================
# LAYER 7: ORCHESTRATION - Event Bus, Services, Lifecycle
# =============================================================================

logger.info("Loading Layer 7: Orchestration Systems...")

# Event Bus
try:
    from trading_bot.core.event_bus import EventBus, Event, EventPriority
    _AVAILABLE['orchestration.event_bus'] = True
except ImportError:
    EventBus = None
    Event = None
    EventPriority = None
    _AVAILABLE['orchestration.event_bus'] = False

# Service Registry
try:
    from trading_bot.core.service_registry import ServiceRegistry, BaseService
    _AVAILABLE['orchestration.registry'] = True
except ImportError:
    ServiceRegistry = None
    BaseService = None
    _AVAILABLE['orchestration.registry'] = False

# Master System
try:
    from trading_bot.master_system import MasterTradingSystem
    _AVAILABLE['orchestration.master'] = True
except ImportError:
    MasterTradingSystem = None
    _AVAILABLE['orchestration.master'] = False

# =============================================================================
# BACKGROUND SERVICES
# =============================================================================

logger.info("Loading Background Services...")

# Sentient Core
try:
    from trading_bot.sentient_core.sentient_orchestrator import SentientOrchestrator
    _AVAILABLE['background.sentient'] = True
except ImportError:
    SentientOrchestrator = None
    _AVAILABLE['background.sentient'] = False

# Eternal Evolution
try:
    from trading_bot.eternal_evolution.eternal_orchestrator import EternalOrchestrator
    _AVAILABLE['background.evolution'] = True
except ImportError:
    EternalOrchestrator = None
    _AVAILABLE['background.evolution'] = False

# Market Student
try:
    from trading_bot.market_student.market_student_orchestrator import MarketStudentOrchestrator
    _AVAILABLE['background.student'] = True
except ImportError:
    MarketStudentOrchestrator = None
    _AVAILABLE['background.student'] = False

# Self Diagnostic
try:
    from trading_bot.self_diagnostic.diagnostic_engine import DiagnosticEngine
    _AVAILABLE['background.diagnostic'] = True
except ImportError:
    DiagnosticEngine = None
    _AVAILABLE['background.diagnostic'] = False

# Monitoring
try:
    from trading_bot.monitoring.performance_monitor import PerformanceMonitor
    _AVAILABLE['background.performance'] = True
except ImportError:
    PerformanceMonitor = None
    _AVAILABLE['background.performance'] = False

# =============================================================================
# BROKER ADAPTERS
# =============================================================================

logger.info("Loading Broker Adapters...")

# MT5 Adapter
try:
    from trading_bot.brokers.mt5_adapter import MT5Adapter
    _AVAILABLE['brokers.mt5'] = True
except ImportError:
    MT5Adapter = None
    _AVAILABLE['brokers.mt5'] = False

# Binance Adapter
try:
    from trading_bot.brokers.binance_adapter import BinanceAdapter
    _AVAILABLE['brokers.binance'] = True
except ImportError:
    BinanceAdapter = None
    _AVAILABLE['brokers.binance'] = False

# Alpaca Adapter
try:
    from trading_bot.brokers.alpaca_adapter import AlpacaAdapter
    _AVAILABLE['brokers.alpaca'] = True
except ImportError:
    AlpacaAdapter = None
    _AVAILABLE['brokers.alpaca'] = False


# =============================================================================
# CONFIGURATION
# =============================================================================

TRADING_CONFIG = {
    'mode': 'paper',  # paper, live
    'symbols': ['EURUSD'],
    'timeframes': ['M5', 'M15', 'H1'],
    'min_confidence': 0.6,
    'max_risk_per_trade': 0.02,
    'max_daily_loss': 0.05,
    'max_drawdown': 0.15,
    'use_ml': True,
    'use_sentiment': False,
    'loop_interval': 5,  # seconds
}


# =============================================================================
# UNIFIED TRADING SYSTEM
# =============================================================================

class UnifiedTradingSystem:
    """
    Unified Trading System - Integrates all modules into one coherent system.
    
    This is the main orchestrator that:
    1. Initializes all layers in correct order
    2. Manages the trading loop
    3. Coordinates between modules
    4. Handles graceful shutdown
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**TRADING_CONFIG, **(config or {})}
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Core components
        self.event_bus = None
        self.service_registry = None
        self.kill_switch = None
        
        # Layer components
        self.mt5 = None
        self.data_manager = None
        self.risk_manager = None
        self.executor = None
        self.strategy_engine = None
        self.signal_engine = None
        
        # Background services
        self.background_tasks: List[asyncio.Task] = []
        
        # Metrics
        self.metrics = {
            'signals_generated': 0,
            'trades_executed': 0,
            'trades_won': 0,
            'trades_lost': 0,
            'total_pnl': 0.0,
            'start_time': None,
        }
        
        logger.info("UnifiedTradingSystem initialized")
    
    async def initialize(self) -> bool:
        """Initialize all system components in correct order."""
        try:
            logger.info("=" * 60)
            logger.info("INITIALIZING UNIFIED TRADING SYSTEM")
            logger.info("=" * 60)
            
            # Layer 0: Safety (ALWAYS FIRST)
            await self._init_safety_layer()
            
            # Layer 7: Orchestration (Event Bus & Registry)
            await self._init_orchestration_layer()
            
            # Layer 1: Data
            await self._init_data_layer()
            
            # Layer 2: Risk
            await self._init_risk_layer()
            
            # Layer 3: Execution
            await self._init_execution_layer()
            
            # Layer 4: Analysis
            await self._init_analysis_layer()
            
            # Layer 5: Signals
            await self._init_signal_layer()
            
            # Layer 6: AI/ML
            await self._init_ml_layer()
            
            # Print status
            self._print_system_status()
            
            self.metrics['start_time'] = datetime.now()
            logger.info("System initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _init_safety_layer(self):
        """Initialize Layer 0: Safety systems."""
        logger.info("Initializing Layer 0: Safety...")
        
        if EmergencyKillSwitch:
            self.kill_switch = EmergencyKillSwitch()
            logger.info("  ✓ Emergency Kill Switch active")
        
        if FailSafeSystem:
            self.fail_safe = FailSafeSystem()
            logger.info("  ✓ Fail-Safe System active")
        
        if CircuitBreaker:
            self.circuit_breaker = CircuitBreaker()
            logger.info("  ✓ Circuit Breaker active")
    
    async def _init_orchestration_layer(self):
        """Initialize Layer 7: Orchestration."""
        logger.info("Initializing Layer 7: Orchestration...")
        
        if EventBus:
            self.event_bus = EventBus()
            logger.info("  ✓ Event Bus initialized")
        
        if ServiceRegistry:
            self.service_registry = ServiceRegistry()
            logger.info("  ✓ Service Registry initialized")
    
    async def _init_data_layer(self):
        """Initialize Layer 1: Data systems."""
        logger.info("Initializing Layer 1: Data...")
        
        if MT5Interface and self.config['mode'] in ['paper', 'live']:
            try:
                self.mt5 = MT5Interface()
                self.mt5.connect()
                logger.info("  ✓ MT5 Interface connected")
            except Exception as e:
                logger.warning(f"  ✗ MT5 connection failed: {e}")
                self.mt5 = None
        
        if DataManager:
            self.data_manager = DataManager()
            logger.info("  ✓ Data Manager initialized")
    
    async def _init_risk_layer(self):
        """Initialize Layer 2: Risk systems."""
        logger.info("Initializing Layer 2: Risk...")
        
        if RiskManager:
            self.risk_manager = RiskManager(
                mt5_interface=self.mt5,
                config={
                    'max_risk_per_trade': self.config['max_risk_per_trade'],
                    'max_daily_loss': self.config['max_daily_loss'],
                    'max_drawdown': self.config['max_drawdown'],
                }
            )
            logger.info("  ✓ Risk Manager initialized")
        
        if DrawdownProtector:
            self.drawdown_protector = DrawdownProtector()
            logger.info("  ✓ Drawdown Protector initialized")
        
        if PreTradeChecker:
            self.pre_trade_checker = PreTradeChecker()
            logger.info("  ✓ Pre-Trade Checker initialized")
    
    async def _init_execution_layer(self):
        """Initialize Layer 3: Execution systems."""
        logger.info("Initializing Layer 3: Execution...")
        
        if self.config['mode'] == 'paper' and PaperExecutor:
            self.executor = PaperExecutor(self.mt5, self.risk_manager)
            logger.info("  ✓ Paper Executor initialized")
        elif self.config['mode'] == 'live' and LiveExecutor:
            self.executor = LiveExecutor(self.mt5, self.risk_manager)
            logger.info("  ✓ Live Executor initialized")
        
        if SmartOrderRouter:
            self.smart_router = SmartOrderRouter()
            logger.info("  ✓ Smart Order Router initialized")
        
        if OrderManager:
            self.order_manager = OrderManager()
            logger.info("  ✓ Order Manager initialized")
    
    async def _init_analysis_layer(self):
        """Initialize Layer 4: Analysis systems."""
        logger.info("Initializing Layer 4: Analysis...")
        
        if MarketStructureAnalyzer:
            self.market_structure = MarketStructureAnalyzer()
            logger.info("  ✓ Market Structure Analyzer initialized")
        
        if LiquidityAnalyzer:
            self.liquidity_analyzer = LiquidityAnalyzer()
            logger.info("  ✓ Liquidity Analyzer initialized")
        
        if MarketRegimeDetector:
            self.regime_detector = MarketRegimeDetector()
            logger.info("  ✓ Market Regime Detector initialized")
        
        if SentimentAnalyzer and self.config.get('use_sentiment'):
            self.sentiment_analyzer = SentimentAnalyzer()
            logger.info("  ✓ Sentiment Analyzer initialized")
    
    async def _init_signal_layer(self):
        """Initialize Layer 5: Signal systems."""
        logger.info("Initializing Layer 5: Signals...")
        
        if self.config.get('use_ml') and MLStrategyEngine:
            self.strategy_engine = MLStrategyEngine(
                self.mt5,
                symbol=self.config['symbols'][0],
                use_price_prediction=True,
                use_pattern_recognition=True,
                use_sentiment=self.config.get('use_sentiment', False)
            )
            logger.info("  ✓ ML Strategy Engine initialized")
        elif StrategyEngine:
            self.strategy_engine = StrategyEngine(
                self.mt5,
                symbol=self.config['symbols'][0]
            )
            logger.info("  ✓ Strategy Engine initialized")
        
        if SignalEngine:
            self.signal_engine = SignalEngine()
            logger.info("  ✓ Signal Engine initialized")
        
        if MultiTimeframeConsensus:
            self.mtf_consensus = MultiTimeframeConsensus()
            logger.info("  ✓ Multi-Timeframe Consensus initialized")
    
    async def _init_ml_layer(self):
        """Initialize Layer 6: AI/ML systems."""
        logger.info("Initializing Layer 6: AI/ML...")
        
        if self.config.get('use_ml'):
            if PredictiveModels:
                self.predictive_models = PredictiveModels()
                logger.info("  ✓ Predictive Models initialized")
            
            if EnsembleModels:
                self.ensemble_models = EnsembleModels()
                logger.info("  ✓ Ensemble Models initialized")
            
            if PatternRecognition:
                self.pattern_recognition = PatternRecognition()
                logger.info("  ✓ Pattern Recognition initialized")
    
    def _print_system_status(self):
        """Print system initialization status."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("SYSTEM STATUS")
        logger.info("=" * 60)
        
        available = sum(1 for v in _AVAILABLE.values() if v)
        total = len(_AVAILABLE)
        
        logger.info(f"Modules loaded: {available}/{total}")
        logger.info(f"Mode: {self.config['mode'].upper()}")
        logger.info(f"Symbols: {', '.join(self.config['symbols'])}")
        logger.info(f"ML Enabled: {self.config.get('use_ml', False)}")
        logger.info(f"Sentiment Enabled: {self.config.get('use_sentiment', False)}")
        
        # Print unavailable modules
        unavailable = [k for k, v in _AVAILABLE.items() if not v]
        if unavailable:
            logger.info(f"Unavailable modules: {len(unavailable)}")
            for mod in unavailable[:10]:  # Show first 10
                logger.debug(f"  - {mod}")
        
        logger.info("=" * 60)
    
    async def run(self):
        """Main trading loop."""
        if not await self.initialize():
            logger.error("Failed to initialize system. Exiting.")
            return
        
        self.running = True
        logger.info("Starting main trading loop...")
        
        # Start background services
        await self._start_background_services()
        
        try:
            while self.running and not self.shutdown_event.is_set():
                try:
                    await self._trading_cycle()
                except Exception as e:
                    logger.error(f"Error in trading cycle: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                await asyncio.sleep(self.config['loop_interval'])
                
        except asyncio.CancelledError:
            logger.info("Trading loop cancelled")
        finally:
            await self.shutdown()
    
    async def _trading_cycle(self):
        """Execute one trading cycle."""
        for symbol in self.config['symbols']:
            try:
                # 1. Fetch market data
                df = await self._fetch_market_data(symbol)
                if df is None or df.empty:
                    continue
                
                # 2. Generate signals
                signals = await self._generate_signals(symbol, df)
                if not signals:
                    continue
                
                # 3. Filter signals by confidence
                best_signal = self._filter_signals(signals)
                if not best_signal:
                    continue
                
                # 4. Pre-trade checks
                if not await self._pre_trade_checks(symbol, best_signal):
                    continue
                
                # 5. Calculate position size
                position_size = await self._calculate_position_size(symbol, best_signal)
                if position_size <= 0:
                    continue
                
                # 6. Execute trade
                await self._execute_trade(symbol, best_signal, position_size)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
    
    async def _fetch_market_data(self, symbol: str):
        """Fetch market data for symbol."""
        if not self.mt5:
            return None
        
        try:
            df = self.mt5.get_rates(symbol, 'M5', 200)
            if df is not None and not df.empty:
                if 'time' in df.columns:
                    df.set_index('time', inplace=True)
            return df
        except Exception as e:
            logger.warning(f"Failed to fetch data for {symbol}: {e}")
            return None
    
    async def _generate_signals(self, symbol: str, df) -> List:
        """Generate trading signals."""
        signals = []
        
        if self.strategy_engine:
            try:
                if hasattr(self.strategy_engine, 'generate_signals'):
                    signals = await self.strategy_engine.generate_signals()
                else:
                    signals = self.strategy_engine.analyse(df)
                self.metrics['signals_generated'] += len(signals) if signals else 0
            except Exception as e:
                logger.warning(f"Signal generation error: {e}")
        
        return signals
    
    def _filter_signals(self, signals) -> Optional[Any]:
        """Filter signals by confidence threshold."""
        min_confidence = self.config['min_confidence']
        best_signal = None
        best_confidence = 0.0
        
        if isinstance(signals, dict):
            conf = signals.get('confidence', signals.get('strength', 0.5))
            if conf >= min_confidence:
                return signals
        elif isinstance(signals, list):
            for sig in signals:
                if hasattr(sig, 'confidence'):
                    conf = sig.confidence / 100.0 if sig.confidence > 1 else sig.confidence
                elif isinstance(sig, dict):
                    conf = sig.get('confidence', sig.get('strength', 0.5))
                else:
                    conf = 0.5
                
                if conf > best_confidence and conf >= min_confidence:
                    best_confidence = conf
                    best_signal = sig
        
        if best_signal:
            logger.info(f"Signal passed confidence gate: {best_confidence:.2f} >= {min_confidence}")
        else:
            logger.debug(f"No signals passed confidence threshold {min_confidence}")
        
        return best_signal
    
    async def _pre_trade_checks(self, symbol: str, signal) -> bool:
        """Run pre-trade safety checks."""
        # Check kill switch
        if self.kill_switch and hasattr(self.kill_switch, 'is_triggered'):
            if self.kill_switch.is_triggered():
                logger.warning("Kill switch triggered - no trading")
                return False
        
        # Check circuit breaker
        if hasattr(self, 'circuit_breaker') and self.circuit_breaker:
            if hasattr(self.circuit_breaker, 'is_open') and self.circuit_breaker.is_open():
                logger.warning("Circuit breaker open - no trading")
                return False
        
        # Check risk manager
        if self.risk_manager and hasattr(self.risk_manager, 'check_drawdown'):
            if not self.risk_manager.check_drawdown():
                logger.warning("Drawdown limit reached - no trading")
                return False
        
        return True
    
    async def _calculate_position_size(self, symbol: str, signal) -> float:
        """Calculate position size for trade."""
        if not self.risk_manager:
            return 0.01  # Minimum fallback
        
        try:
            stop_loss_pips = 20  # Default
            if hasattr(signal, 'stop_loss_pips'):
                stop_loss_pips = signal.stop_loss_pips
            elif isinstance(signal, dict):
                stop_loss_pips = signal.get('stop_loss_pips', 20)
            
            pos = self.risk_manager.calculate_position_size(
                symbol=symbol,
                stop_loss_pips=stop_loss_pips
            )
            
            if hasattr(pos, 'lot') and pos.lot > 0:
                return pos.lot
            elif isinstance(pos, (int, float)) and pos > 0:
                return pos
            else:
                logger.warning("Position size calculation returned 0, using fallback")
                return 0.01
                
        except Exception as e:
            logger.warning(f"Position sizing error: {e}, using fallback")
            return 0.01
    
    async def _execute_trade(self, symbol: str, signal, size: float):
        """Execute the trade."""
        if not self.executor:
            logger.error("No executor available")
            return
        
        # Determine direction
        direction = 1  # Default buy
        if hasattr(signal, 'direction'):
            direction = -1 if str(signal.direction).lower() in ('sell', 'short', '-1') else 1
        elif isinstance(signal, dict):
            sig_dir = signal.get('direction', signal.get('action', 'buy'))
            direction = -1 if str(sig_dir).lower() in ('sell', 'short', '-1') else 1
        
        # Cap size
        size = min(size, 10.0)  # Max 10 lots
        
        logger.info(f"EXECUTING: {symbol} {'BUY' if direction > 0 else 'SELL'} {size} lots")
        
        try:
            await self.executor.execute_trade(
                symbol=symbol,
                direction=direction,
                size=size
            )
            self.metrics['trades_executed'] += 1
            logger.info(f"Trade executed successfully!")
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
    
    async def _start_background_services(self):
        """Start background services."""
        logger.info("Starting background services...")
        
        # These run in the background without blocking
        if SentientOrchestrator and _AVAILABLE.get('background.sentient'):
            task = asyncio.create_task(self._run_sentient_service())
            self.background_tasks.append(task)
            logger.info("  ✓ Sentient Core service started")
        
        if EternalOrchestrator and _AVAILABLE.get('background.evolution'):
            task = asyncio.create_task(self._run_evolution_service())
            self.background_tasks.append(task)
            logger.info("  ✓ Eternal Evolution service started")
        
        if MarketStudentOrchestrator and _AVAILABLE.get('background.student'):
            task = asyncio.create_task(self._run_student_service())
            self.background_tasks.append(task)
            logger.info("  ✓ Market Student service started")
    
    async def _run_sentient_service(self):
        """Run sentient core service."""
        try:
            orchestrator = SentientOrchestrator()
            await orchestrator.start()
        except Exception as e:
            logger.error(f"Sentient service error: {e}")
    
    async def _run_evolution_service(self):
        """Run eternal evolution service."""
        try:
            orchestrator = EternalOrchestrator()
            await orchestrator.start()
        except Exception as e:
            logger.error(f"Evolution service error: {e}")
    
    async def _run_student_service(self):
        """Run market student service."""
        try:
            orchestrator = MarketStudentOrchestrator()
            await orchestrator.start()
        except Exception as e:
            logger.error(f"Student service error: {e}")
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Initiating graceful shutdown...")
        self.running = False
        self.shutdown_event.set()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Close MT5 connection
        if self.mt5:
            try:
                self.mt5.shutdown()
            except Exception:
                pass
        
        # Print final metrics
        self._print_final_metrics()
        
        logger.info("Shutdown complete")
    
    def _print_final_metrics(self):
        """Print final trading metrics."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("FINAL METRICS")
        logger.info("=" * 60)
        logger.info(f"Signals Generated: {self.metrics['signals_generated']}")
        logger.info(f"Trades Executed: {self.metrics['trades_executed']}")
        if self.metrics['start_time']:
            runtime = datetime.now() - self.metrics['start_time']
            logger.info(f"Runtime: {runtime}")
        logger.info("=" * 60)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Trading Bot - Unified System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['paper', 'live'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    
    parser.add_argument(
        '--symbol', '-s',
        type=str,
        default='EURUSD',
        help='Trading symbol (default: EURUSD)'
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        nargs='+',
        help='Multiple trading symbols'
    )
    
    parser.add_argument(
        '--use-ml',
        action='store_true',
        default=True,
        help='Enable ML-based strategies (default: True)'
    )
    
    parser.add_argument(
        '--no-ml',
        action='store_true',
        help='Disable ML-based strategies'
    )
    
    parser.add_argument(
        '--use-sentiment',
        action='store_true',
        help='Enable sentiment analysis'
    )
    
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.6,
        help='Minimum signal confidence (default: 0.6)'
    )
    
    parser.add_argument(
        '--max-risk',
        type=float,
        default=0.02,
        help='Maximum risk per trade (default: 0.02)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Trading loop interval in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build config from args
    config = {
        'mode': args.mode,
        'symbols': args.symbols or [args.symbol],
        'use_ml': not args.no_ml and args.use_ml,
        'use_sentiment': args.use_sentiment,
        'min_confidence': args.min_confidence,
        'max_risk_per_trade': args.max_risk,
        'loop_interval': args.interval,
    }
    
    # Create and run system
    system = UnifiedTradingSystem(config)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        system.shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    await system.run()


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     █████╗ ██╗     ██████╗ ██╗  ██╗ █████╗                   ║
    ║    ██╔══██╗██║     ██╔══██╗██║  ██║██╔══██╗                  ║
    ║    ███████║██║     ██████╔╝███████║███████║                  ║
    ║    ██╔══██║██║     ██╔═══╝ ██╔══██║██╔══██║                  ║
    ║    ██║  ██║███████╗██║     ██║  ██║██║  ██║                  ║
    ║    ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝                  ║
    ║                                                               ║
    ║            ALGO TRADING SYSTEM v2.0                          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
