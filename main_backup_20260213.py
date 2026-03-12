from __future__ import annotations
import sys
import logging

# Fix Windows console encoding for emoji in log messages
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    # Also patch existing logging StreamHandlers
    for _h in logging.root.handlers:
        if isinstance(_h, logging.StreamHandler) and hasattr(_h.stream, 'reconfigure'):
            try:
                _h.stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

"""CLI entry point for the Advanced Algorithmic Trading Bot.

This is the main entry point for the trading bot with support for:
1. Traditional technical analysis strategies
2. Advanced ML/AI predictive models with transformer-based deep learning
3. Reinforcement learning with PPO for strategy optimization
4. Execution optimization algorithms (TWAP, VWAP, Smart)
5. Emotional state tracking and enhanced performance analytics
6. Market structure, liquidity, and order flow analysis

Usage (paper-mode by default – no orders are sent):
    python main.py --symbol EURUSD --timeframe M15 --bars 200
    
Advanced usage:
    python main.py --symbol EURUSD --timeframe H1 --bars 500 --mode paper --use-ml --execution-algo smart
    python main.py --symbol EURUSD --timeframe H1 --bars 1000 --use-ml --use-transformer --use-rl
"""

import argparse
import os
from typing import Any, Dict, List, Optional, Union
import asyncio
import contextlib
from loguru import logger
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Utility helpers (imported from trading_bot.utils.safe_access)
# ---------------------------------------------------------------------------

# Strategy modules
from trading_bot.strategy import StrategyEngine, MLStrategyEngine

# Execution modules
try:
    from trading_bot.execution import PaperExecutor, TWAPExecutor, VWAPExecutor, SmartOrderRouter
except ImportError:
    from trading_bot.execution.paper_executor import PaperExecutor
    from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.execution.live_executor import LiveExecutor

# Analytics modules
from trading_bot.analytics import PerformanceAnalytics, EmotionalStateTracker, EnhancedPerformanceAnalytics

# Core modules
from trading_bot.config import get
from trading_bot.data import MT5Interface
from trading_bot.reporting import init_logger
from trading_bot.utils import profile_function
from trading_bot.utils.safe_access import safe_get
from trading_bot.risk import RiskManager

# Internet connectivity modules
from trading_bot.connectivity.web_client import WebClient
from trading_bot.connectivity.api_client import APIClient, AlphaVantageClient, YahooFinanceClient
from trading_bot.connectivity.websocket_client import WebsocketClient, BinanceWebsocketClient
from trading_bot.connectivity.auth_manager import AuthManager
from trading_bot.connectivity.rate_limiter import RateLimiter, create_common_rate_limiter
from trading_bot.connectivity.proxy_manager import ProxyManager
from trading_bot.connectivity.cache_manager import CacheManager
from trading_bot.connectivity.web_scraper import WebScraper, FinancialNewsScraper

# Intelligence modules
from trading_bot.intel.news_pipeline import NewsPipeline, NewsSignal
from trading_bot.intel.strategy_researcher import StrategyResearcher
from trading_bot.intel.fundamental_analyzer import FundamentalAnalyzer

# Safety systems
try:
    from trading_bot.safety import (
        EmergencyKillSwitch,
        LatencyCircuitBreaker,
        ResourceWatchdog,
        ConnectivityMonitor,
        AutoPauseManager
    )
    SAFETY_SYSTEMS_AVAILABLE = True
except ImportError:
    SAFETY_SYSTEMS_AVAILABLE = False
    logger.warning("Safety systems not available - proceeding without safety features")

# Offline RL systems
try:
    from trading_bot.ml.offline_rl import (
        CQLAgent,
        BCQAgent,
        ContinuousLearningOrchestrator,
        DatasetBuilder
    )
    RL_SYSTEMS_AVAILABLE = True
except ImportError:
    RL_SYSTEMS_AVAILABLE = False
    logger.warning("Offline RL systems not available")

# ---------------------------------------------------------------------------
# Extended modules (moved from archive directories)
# ---------------------------------------------------------------------------

# Multi-Agent System
try:
    from trading_bot.agents2 import MultiAgentCoordinator, TrendFollowingAgent, MeanReversionAgent, VolatilityAgent, RiskManagerAgent, MarketMakerAgent
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    logger.warning("Multi-agent system not available")

# Advanced Systems 2 (Red Team / Blue Team)
try:
    from trading_bot.advanced_systems2 import RedTeamBlueTeam
    ADVANCED_SYSTEMS2_AVAILABLE = True
except ImportError:
    ADVANCED_SYSTEMS2_AVAILABLE = False
    logger.warning("Advanced Systems 2 not available")

# Automation (Trade Journal)
try:
    from trading_bot.automation import TradeJournal, TradeEntry
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    logger.warning("Automation module not available")

# Compliance
try:
    from trading_bot.compliance import ComplianceMonitor
    COMPLIANCE_AVAILABLE = True
except ImportError:
    COMPLIANCE_AVAILABLE = False
    logger.warning("Compliance module not available")

# Broker Integration
try:
    from trading_bot.broker import BrokerInterface, BinanceBroker
    BROKER_AVAILABLE = True
except ImportError:
    BROKER_AVAILABLE = False
    logger.warning("Broker integration not available")

# Learning (RL + Strategy Optimizer)
try:
    from trading_bot.learning import PerformanceAnalyzer, StrategyOptimizer
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False
    logger.warning("Learning module not available")

# Infrastructure (Health, Monitoring, Scaling)
try:
    from trading_bot.infrastructure import HealthCheck, PerformanceMonitor, AutoScaler
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    logger.warning("Infrastructure module not available")

# Multimodal Intelligence
try:
    from trading_bot.multimodal import MultimodalFusion, PriceEncoder, NewsEncoder
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False
    logger.warning("Multimodal intelligence not available")

# Neuro-Symbolic Reasoning
try:
    from trading_bot.reasoning import ChainOfThoughtReasoner, FinancialKnowledgeGraph, NeuroSymbolicFusion
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    logger.warning("Reasoning module not available")

# Superintelligence
try:
    from trading_bot.superintelligence import SuperintelligenceOrchestrator, MultiBrainEnsemble, RegimeStrategyEngine, SelfOptimizingCore, SelfRegulationEngine, MemorySystems
    SUPERINTELLIGENCE_AVAILABLE = True
except ImportError:
    SUPERINTELLIGENCE_AVAILABLE = False
    logger.warning("Superintelligence module not available")

# Archive Orchestrator (126 archive modules)
try:
    from trading_bot.archive_orchestrator import ArchiveOrchestrator
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive orchestrator not available")

# Recursive Self-Improvement System
try:
    from trading_bot.recursive_improvement import (
        RecursiveImprovementOrchestrator,
        RecursiveImprovementCore,
        RecursiveStrategyEvolution,
        RecursiveRiskOptimization,
        RecursiveExecutionOptimization,
        MetaRecursiveController,
    )
    RECURSIVE_IMPROVEMENT_AVAILABLE = True
except ImportError:
    RECURSIVE_IMPROVEMENT_AVAILABLE = False
    logger.warning("Recursive self-improvement system not available")

# Self-Improvement Engine
try:
    from trading_bot.self_improvement import (
        SelfImprovementOrchestrator,
        SelfImprovementEngine,
        ContinuousLearner,
        TradeTriage,
    )
    SELF_IMPROVEMENT_AVAILABLE = True
except ImportError:
    SELF_IMPROVEMENT_AVAILABLE = False
    logger.warning("Self-improvement engine not available")

# Cognitive Architecture
try:
    from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore
    COGNITIVE_AVAILABLE = True
except ImportError:
    COGNITIVE_AVAILABLE = False
    logger.warning("Cognitive architecture not available")

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:  # noqa: D401 – imperative style
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Advanced Algorithmic Trading Bot for MetaTrader 5",
    )
    parser.add_argument(
        "--symbol",
        help="Primary trading symbol, e.g. EURUSD. Defaults to config value or EURUSD.",
        default=None,
    )
    parser.add_argument(
        "--additional-symbols",
        help="Additional trading symbols as comma-separated list, e.g. GBPUSD,USDJPY",
        default=None,
    )
    parser.add_argument(
        "--timeframe",
        help="MT5 timeframe key (M1, M5, M15, H1,…). Defaults to M15.",
        default="M15",
    )
    parser.add_argument(
        "--bars",
        help="Number of bars to fetch for analysis.",
        type=int,
        default=200,
    )
    parser.add_argument(
        "--mode",
        choices=["smoke", "paper", "live"],
        default="paper",
        help="Execution mode: smoke=test connectivity, paper=simulate orders.",
    )
    parser.add_argument(
        "--log-level",
        help="Override logging level (DEBUG | INFO | WARNING | ERROR | CRITICAL).",
        default=None,
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable performance profiling.",
        default=False,
    )
    parser.add_argument(
        "--use-ml",
        action="store_true",
        help="Use ML-enhanced strategy engine.",
        default=False,
    )
    parser.add_argument(
        "--use-transformer",
        action="store_true",
        help="Use transformer-based deep learning model for price prediction.",
        default=False,
    )
    parser.add_argument(
        "--use-rl",
        action="store_true",
        help="Use reinforcement learning (PPO) for strategy optimization.",
        default=False,
    )
    parser.add_argument(
        "--market-regime",
        action="store_true",
        help="Enable market regime classification.",
        default=False,
    )
    parser.add_argument(
        "--execution-algo",
        choices=["default", "twap", "vwap", "smart"],
        default="default",
        help="Execution algorithm to use.",
    )
    parser.add_argument(
        "--track-emotions",
        action="store_true",
        help="Enable emotional state tracking.",
        default=False,
    )
    parser.add_argument(
        "--sentiment-analysis",
        action="store_true",
        help="Enable market sentiment analysis.",
        default=False,
    )
    # API keys should be loaded from environment variables or .env file
    # Removed --news-api-key argument for security (keys visible in process list)
    parser.add_argument(
        "--news-data-dir",
        help="Directory for storing news data.",
        default="./data/news",
    )
    parser.add_argument(
        "--strategy-research",
        action="store_true",
        help="Enable strategy research and learning from external sources.",
        default=False,
    )
    parser.add_argument(
        "--fundamental-analysis",
        action="store_true",
        help="Enable fundamental analysis (macro, company, on-chain data).",
        default=False,
    )
    # API keys should be loaded from environment variables or .env file
    # Removed --fred-api-key argument for security (keys visible in process list)
    parser.add_argument(
        "--research-data-dir",
        help="Directory for storing research and fundamental data.",
        default="./data/research",
    )
    parser.add_argument(
        "--order-flow",
        action="store_true",
        help="Enable order flow analysis.",
        default=False,
    )
    parser.add_argument(
        "--quantum-blockchain",
        action="store_true",
        help="Enable quantum computing and blockchain validation features.",
        default=False,
    )
    parser.add_argument(
        "--adaptive-mode",
        action="store_true",
        help="Enable full adaptive trading system with self-improvement capabilities.",
        default=False,
    )
    parser.add_argument(
        "--self-improve",
        action="store_true",
        help="Enable self-improvement capabilities for the trading bot.",
        default=False,
    )
    parser.add_argument(
        "--internet-access",
        action="store_true",
        help="Enable internet access for real-time data and news.",
        default=False,
    )
    parser.add_argument(
        "--api-source",
        choices=["alphavantage", "yahoo", "binance", "all"],
        default="yahoo",
        help="API data source to use for market data.",
    )
    parser.add_argument(
        "--websocket-feed",
        action="store_true",
        help="Enable real-time websocket data feed.",
        default=False,
    )
    parser.add_argument(
        "--news-scraping",
        action="store_true",
        help="Enable news scraping from financial websites.",
        default=False,
    )
    parser.add_argument(
        "--cache-dir",
        help="Directory for caching data.",
        default="./cache",
    )
    parser.add_argument(
        "--api-keys-file",
        help="Path to API keys file.",
        default="./config/api_keys.json",
    )
    parser.add_argument(
        "--manage-correlations",
        action="store_true",
        help="Enable correlation management for multi-symbol trading.",
        default=False,
    )
    parser.add_argument(
        "--max-correlated-exposure",
        type=int,
        help="Maximum percentage of capital in correlated pairs (1-100).",
        default=50,
    )
    
    # Integrated systems flags
    parser.add_argument(
        "--orchestrator",
        action="store_true",
        help="Enable master orchestrator system for multi-strategy coordination.",
        default=False,
    )
    parser.add_argument(
        "--enable-scanners",
        action="store_true",
        help="Enable opportunity scanners (market inefficiency, arbitrage, momentum).",
        default=False,
    )
    parser.add_argument(
        "--advanced-exits",
        action="store_true",
        help="Enable advanced exit strategies (adaptive, profit maximizer, trailing).",
        default=False,
    )
    parser.add_argument(
        "--adaptive",
        action="store_true",
        help="Enable adaptive systems (regime detection, strategy selection, self-improvement).",
        default=False,
    )
    parser.add_argument(
        "--full-integration",
        action="store_true",
        help="Enable all integrated systems (orchestrator, scanners, exits, adaptive, risk).",
        default=False,
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Enable real-time dashboard server.",
        default=False,
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        help="Dashboard server port (default: 8050).",
        default=8050,
    )
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run backtesting mode instead of live/paper trading.",
        default=False,
    )
    parser.add_argument(
        "--start-date",
        help="Backtest start date (YYYY-MM-DD).",
        default=None,
    )
    parser.add_argument(
        "--end-date",
        help="Backtest end date (YYYY-MM-DD).",
        default=None,
    )
    parser.add_argument(
        "--trading-mode",
        choices=["aggressive", "balanced", "conservative", "defensive", "scalping", "swing", "position"],
        help="Trading mode for orchestrator (default: balanced).",
        default="balanced",
    )
    
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Multi-symbol trading functionality
# ---------------------------------------------------------------------------

class MultiSymbolTrader:
    """Handles trading operations for multiple symbols simultaneously."""
    
    def __init__(self, primary_symbol: str, additional_symbols: list[str], 
                 timeframe: str, bars: int, manage_correlations: bool = False,
                 max_correlated_exposure: int = 50):
        self.primary_symbol = primary_symbol
        self.additional_symbols = additional_symbols
        self.timeframe = timeframe
        self.bars = bars
        self.manage_correlations = manage_correlations
        self.max_correlated_exposure = max_correlated_exposure
        self.correlation_matrix = None
        self.symbol_data = {}
        self.traders = {}
        
    async def initialize(self, args: argparse.Namespace) -> None:
        """Initialize traders for all symbols."""
        # Initialize primary symbol
        logger.info(f"Initializing primary symbol: {self.primary_symbol}")
        self.traders[self.primary_symbol] = await self._create_trader(self.primary_symbol, args)
        
        # Initialize additional symbols
        for symbol in self.additional_symbols:
            logger.info(f"Initializing additional symbol: {symbol}")
            self.traders[symbol] = await self._create_trader(symbol, args)
            
        # Calculate initial correlations if enabled
        if self.manage_correlations:
            await self.update_correlations()
    
    async def _create_trader(self, symbol: str, args: argparse.Namespace) -> Any:
        """Create a trader instance for a single symbol."""
        # Initialize MT5 interface (paper/live depends on args.mode via config)
        mt5i = MT5Interface()
        
        # Create strategy engine
        strategy_engine = self._create_strategy_engine(symbol, args, mt5i)
        
        # Create risk manager
        risk_manager = RiskManager(mt5i)
        
        # Select executor using global helper
        executor = _select_executor(mt5i, risk_manager, args.mode, args.execution_algo)
        
        return {
            'strategy': strategy_engine,
            'risk': risk_manager,
            'executor': executor
        }

    def _create_strategy_engine(self, symbol: str, args: argparse.Namespace, mt5i) -> Any:
        """Create a strategy engine for a single symbol."""
        if args.use_ml:
            # MLStrategyEngine accepts: use_price_prediction, use_pattern_recognition, use_sentiment
            return MLStrategyEngine(
                mt5i,
                symbol=symbol,
                use_price_prediction=True,
                use_pattern_recognition=True,
                use_sentiment=getattr(args, 'sentiment_analysis', False)
            )
        else:
            return StrategyEngine(mt5i, symbol=symbol)
    
    async def update_correlations(self) -> None:
        """Update correlation matrix for all traded symbols."""
        if not self.manage_correlations:
            return
            
        try:
            # Get mt5_interface from one of the traders
            if not self.traders:
                logger.warning("No traders initialized, cannot update correlations")
                return
                
            # Get mt5 interface from first trader's strategy
            first_trader = next(iter(self.traders.values()))
            mt5_interface = first_trader['strategy'].mt5 if hasattr(first_trader['strategy'], 'mt5') else None
            
            if mt5_interface is None:
                logger.warning("MT5 interface not available, skipping correlation update")
                return
            
            # Get price data for all symbols
            all_symbols = [self.primary_symbol] + self.additional_symbols
            price_data = {}
            
            for symbol in all_symbols:
                data = await mt5_interface.get_rates(symbol, self.timeframe, self.bars)
                if data is not None:
                    price_data[symbol] = pd.DataFrame(data)['close']
            
            # Calculate correlation matrix
            if price_data:
                df = pd.DataFrame(price_data)
                self.correlation_matrix = df.corr()
                logger.info("Updated correlation matrix")
                logger.debug(f"Correlation matrix:\n{self.correlation_matrix}")
        
        except Exception as e:
            logger.error(f"Error updating correlations: {e}")
    
    def adjust_position_sizes(self, positions: dict) -> dict:
        """Adjust position sizes based on correlations."""
        if not self.manage_correlations or self.correlation_matrix is None:
            return positions
            
        try:
            adjusted_positions = {}
            
            # Calculate total correlation exposure for each symbol
            correlation_scores = {}
            for symbol1 in positions.keys():
                total_corr = 0
                for symbol2 in positions.keys():
                    if symbol1 != symbol2:
                        corr = abs(self.correlation_matrix.loc[symbol1, symbol2])
                        total_corr += corr
                correlation_scores[symbol1] = total_corr
            
            # Adjust positions: lower correlation = higher weight
            max_corr = max(correlation_scores.values()) if correlation_scores else 1.0
            for symbol, pos in positions.items():
                # Inverse correlation weighting: less correlated symbols get larger size
                corr_factor = 1.0 - (correlation_scores[symbol] / max_corr) if max_corr > 0 else 1.0
                # Apply max exposure limit
                exposure_limit = self.max_correlated_exposure / 100.0
                adjusted_positions[symbol] = pos * corr_factor * exposure_limit
            
            return adjusted_positions
            
        except Exception as e:
            logger.error(f"Error adjusting position sizes: {e}")
            return positions
    
    async def process_symbols(self) -> None:
        """Process all symbols and execute trades."""
        try:
            # Update correlations first
            if self.manage_correlations:
                await self.update_correlations()
            
            # Process each symbol
            positions = {}
            for symbol, trader in self.traders.items():
                # Get trading signals
                signals = await trader['strategy'].generate_signals()
                position = 0
                if isinstance(signals, list):
                    for signal in signals:
                        stop_loss_pips = safe_get(signal, 'stop_loss_pips', 20)
                        try:
                            pos = trader['risk'].calculate_position_size(symbol=symbol, stop_loss_pips=stop_loss_pips)
                            if hasattr(pos, 'lot') and pos.lot > 0:
                                position = pos
                                break
                            elif pos != 0:
                                position = pos
                                break
                        except Exception as e:
                            logger.warning(f"Skipping signal due to error: {e}")
                elif isinstance(signals, dict):
                    stop_loss_pips = safe_get(signals, 'stop_loss_pips', 20)
                    try:
                        position = trader['risk'].calculate_position_size(symbol=symbol, stop_loss_pips=stop_loss_pips)
                        if hasattr(position, 'lot') and position.lot > 0:
                            positions[symbol] = position
                        elif position != 0:
                            positions[symbol] = position
                    except Exception as e:
                        logger.warning(f"Skipping signal due to error: {e}")
            
            # Adjust positions based on correlations
            if self.manage_correlations and positions:
                positions = self.adjust_position_sizes(positions)
            
            # Execute trades
            for symbol, position in positions.items():
                if hasattr(position, 'lot') and position.lot > 0:
                    await self.traders[symbol]['executor'].execute_trade(
                        symbol=symbol,
                        direction=1 if position.lot > 0 else -1,
                        size=abs(position.lot)
                    )
                elif position != 0:
                    await self.traders[symbol]['executor'].execute_trade(
                        symbol=symbol,
                        direction=1 if position > 0 else -1,
                        size=abs(position)
                    )
        except Exception as e:
            logger.error(f"Error processing symbols: {e}")

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

@profile_function("INFO")
async def main(argv: list[str] | None = None) -> None:  # noqa: D401 – imperative style
    args = parse_args(argv)

    # ------------------------------------------------------------------
    # Initialise logging
    # ------------------------------------------------------------------
    init_logger(level=args.log_level)
    
    # ------------------------------------------------------------------
    # Initialize safety systems
    # ------------------------------------------------------------------
    safety_systems = {}
    if SAFETY_SYSTEMS_AVAILABLE:
        try:
            safety_systems['kill_switch'] = EmergencyKillSwitch()
            safety_systems['latency_breaker'] = LatencyCircuitBreaker()
            safety_systems['watchdog'] = ResourceWatchdog()
            safety_systems['connectivity'] = ConnectivityMonitor()
            safety_systems['auto_pause'] = AutoPauseManager()
            logger.info("Safety systems initialized: kill_switch, latency_breaker, watchdog, connectivity, auto_pause")
        except Exception as e:
            logger.error("Failed to initialize safety systems: {}", e)
            safety_systems = {}
    
    # Initialize RL systems
    rl_systems = {}
    if RL_SYSTEMS_AVAILABLE:
        try:
            rl_systems['cql_agent'] = CQLAgent()
            rl_systems['bcq_agent'] = BCQAgent()
            rl_systems['rl_orchestrator'] = ContinuousLearningOrchestrator()
            rl_systems['dataset_builder'] = DatasetBuilder()
            logger.info("Offline RL systems initialized: CQL, BCQ, orchestrator, dataset_builder")
        except Exception as e:
            logger.error("Failed to initialize RL systems: {}", e)
            rl_systems = {}
    
    # ------------------------------------------------------------------
    # Initialize extended modules (agents, reasoning, superintelligence, etc.)
    # ------------------------------------------------------------------
    extended_systems = {}
    
    if AGENTS_AVAILABLE:
        try:
            agents = {
                'trend': TrendFollowingAgent(),
                'mean_reversion': MeanReversionAgent(),
                'volatility': VolatilityAgent(),
                'risk_manager': RiskManagerAgent(),
                'market_maker': MarketMakerAgent(),
            }
            extended_systems['agent_coordinator'] = MultiAgentCoordinator(agents)
            logger.info("Multi-agent system initialized with 5 agents")
        except Exception as e:
            logger.error("Failed to initialize multi-agent system: {}", e)
    
    if ADVANCED_SYSTEMS2_AVAILABLE:
        try:
            extended_systems['red_team_blue_team'] = RedTeamBlueTeam()
            logger.info("Red Team / Blue Team adversarial system initialized")
        except Exception as e:
            logger.error("Failed to initialize advanced systems 2: {}", e)
    
    if AUTOMATION_AVAILABLE:
        try:
            extended_systems['trade_journal'] = TradeJournal()
            logger.info("Trade journal automation initialized")
        except Exception as e:
            logger.error("Failed to initialize trade journal: {}", e)
    
    if COMPLIANCE_AVAILABLE:
        try:
            extended_systems['compliance'] = ComplianceMonitor()
            logger.info("Compliance monitor initialized")
        except Exception as e:
            logger.error("Failed to initialize compliance: {}", e)
    
    if BROKER_AVAILABLE:
        try:
            extended_systems['broker_interface'] = BrokerInterface
            logger.info("Broker integration available (BinanceBroker, IBBroker)")
        except Exception as e:
            logger.error("Failed to initialize broker integration: {}", e)
    
    if LEARNING_AVAILABLE:
        try:
            extended_systems['performance_analyzer'] = PerformanceAnalyzer()
            extended_systems['strategy_optimizer'] = StrategyOptimizer()
            logger.info("Learning module initialized (PerformanceAnalyzer, StrategyOptimizer)")
        except Exception as e:
            logger.error("Failed to initialize learning module: {}", e)
    
    if INFRASTRUCTURE_AVAILABLE:
        try:
            extended_systems['health_check'] = HealthCheck()
            extended_systems['performance_monitor'] = PerformanceMonitor()
            logger.info("Infrastructure initialized (HealthCheck, PerformanceMonitor)")
        except Exception as e:
            logger.error("Failed to initialize infrastructure: {}", e)
    
    if MULTIMODAL_AVAILABLE:
        try:
            extended_systems['multimodal_fusion'] = MultimodalFusion()
            logger.info("Multimodal intelligence initialized")
        except Exception as e:
            logger.error("Failed to initialize multimodal: {}", e)
    
    if REASONING_AVAILABLE:
        try:
            extended_systems['reasoner'] = ChainOfThoughtReasoner()
            extended_systems['knowledge_graph'] = FinancialKnowledgeGraph()
            extended_systems['neuro_symbolic'] = NeuroSymbolicFusion()
            logger.info("Neuro-symbolic reasoning initialized")
        except Exception as e:
            logger.error("Failed to initialize reasoning: {}", e)
    
    if SUPERINTELLIGENCE_AVAILABLE:
        try:
            si_orchestrator = SuperintelligenceOrchestrator()
            si_orchestrator.initialize()
            extended_systems['superintelligence'] = si_orchestrator
            extended_systems['multi_brain'] = MultiBrainEnsemble()
            extended_systems['regime_engine'] = RegimeStrategyEngine()
            extended_systems['self_optimizer'] = SelfOptimizingCore()
            extended_systems['self_regulation'] = SelfRegulationEngine()
            extended_systems['memory_systems'] = MemorySystems()
            logger.info("Superintelligence module initialized (6 components)")
        except Exception as e:
            logger.error("Failed to initialize superintelligence: {}", e)
    
    # Archive Orchestrator (126 archive modules)
    if ARCHIVE_AVAILABLE:
        try:
            extended_systems['archive_orchestrator'] = ArchiveOrchestrator()
            logger.info("Archive orchestrator initialized with %d modules",
                        len(extended_systems['archive_orchestrator'].modules))
        except Exception as e:
            logger.error("Failed to initialize archive orchestrator: {}", e)

    # ------------------------------------------------------------------
    # Initialize Recursive Self-Improvement System
    # ------------------------------------------------------------------
    recursive_system = None
    if RECURSIVE_IMPROVEMENT_AVAILABLE:
        try:
            recursive_config = {
                'core': {'max_depth': 5, 'convergence_threshold': 0.01},
                'strategy': {'mutation_rate': 0.1, 'population_size': 20},
                'risk': {'adaptation_speed': 0.05},
                'execution': {'slippage_target_bps': 1.0},
                'learning': {'meta_learning_rate': 0.001},
            }
            recursive_system = RecursiveImprovementOrchestrator(recursive_config)
            extended_systems['recursive_improvement'] = recursive_system
            logger.info("Recursive self-improvement system initialized (strategy, risk, execution, learning, architecture)")
        except Exception as e:
            logger.error("Failed to initialize recursive self-improvement: {}", e)
    
    if SELF_IMPROVEMENT_AVAILABLE:
        try:
            si_engine = SelfImprovementEngine()
            extended_systems['self_improvement_engine'] = si_engine
            
            continuous_learner = ContinuousLearner()
            extended_systems['continuous_learner'] = continuous_learner
            
            trade_triage = TradeTriage()
            extended_systems['trade_triage'] = trade_triage
            logger.info("Self-improvement engine initialized (engine, learner, triage)")
        except Exception as e:
            logger.error("Failed to initialize self-improvement engine: {}", e)
    
    # Initialize Cognitive Architecture
    cognitive_core = None
    if COGNITIVE_AVAILABLE:
        try:
            cognitive_core = AlphaAlgoCognitiveCore()
            extended_systems['cognitive_core'] = cognitive_core
            logger.info("Cognitive architecture initialized (10-layer decision pipeline)")
        except Exception as e:
            logger.error("Failed to initialize cognitive architecture: {}", e)

    logger.info("Extended systems initialized: {} modules active", len(extended_systems))
    
    # ------------------------------------------------------------------
    # PROFITABILITY OBJECTIVE
    # ------------------------------------------------------------------
    # The SOLE objective of this trading bot is to be PROFITABLE.
    # Every decision, every signal, every trade must be evaluated against
    # this single criterion: does it increase expected profit?
    # ------------------------------------------------------------------
    PROFITABILITY_CONFIG = {
        'objective': 'MAXIMIZE_PROFIT',
        'min_confidence': 0.6,
        'min_risk_reward': 1.5,
        'max_risk_per_trade': 0.02,
        'max_daily_loss': 0.05,
        'max_drawdown': 0.15,
        'profit_target_daily': 0.005,
        'use_real_data_only': True,
        'never_use_mock_data': True,
        'adapt_to_market': True,
        'learn_from_losses': True,
        'compound_winners': True,
    }
    logger.info("=" * 70)
    logger.info("TRADING BOT OBJECTIVE: PROFITABILITY")
    logger.info("  - Using REAL-TIME market data from MT5 (no mock data)")
    logger.info("  - Min confidence: {}", PROFITABILITY_CONFIG['min_confidence'])
    logger.info("  - Min risk/reward: {}", PROFITABILITY_CONFIG['min_risk_reward'])
    logger.info("  - Max risk per trade: {}%", PROFITABILITY_CONFIG['max_risk_per_trade'] * 100)
    logger.info("  - Recursive self-improvement: {}", "ACTIVE" if recursive_system else "OFF")
    logger.info("=" * 70)
    
    # ------------------------------------------------------------------
    # Handle integrated systems modes
    # ------------------------------------------------------------------
    
    # Check if full integration is requested
    if args.full_integration:
        args.orchestrator = True
        args.enable_scanners = True
        args.advanced_exits = True
        args.adaptive = True
        logger.info("Full integration mode enabled - activating all systems")
    
    # Run dashboard if requested
    if args.dashboard:
        logger.info("Starting dashboard server on port {}...", args.dashboard_port)
        try:
            from trading_bot import UnifiedDashboard
            dashboard = UnifiedDashboard()
            await dashboard.start(port=args.dashboard_port)
            return
        except ImportError as e:
            logger.error("Dashboard not available: {}", e)
            logger.info("Run: python validate_integrations.py to check integration status")
            sys.exit(1)
    
    # Run backtesting if requested
    if args.backtest:
        if not args.start_date or not args.end_date:
            logger.error("Backtest mode requires --start-date and --end-date")
            sys.exit(1)
        
        logger.info("Starting backtest mode...")
        try:
            from trading_bot import AdvancedBacktester, TestMode
            
            backtester = AdvancedBacktester(
                strategy=None,  # Will use default strategy
                test_mode=TestMode.MONTE_CARLO
            )
            
            results = await backtester.run(
                symbol=args.symbol or "EURUSD",
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            logger.info("=" * 80)
            logger.info("BACKTEST RESULTS")
            logger.info("=" * 80)
            logger.info("Total Trades: {}", results.total_trades)
            logger.info("Win Rate: {:.2%}", results.win_rate)
            logger.info("Profit Factor: {:.2f}", results.profit_factor)
            logger.info("Sharpe Ratio: {:.2f}", results.sharpe_ratio)
            logger.info("Max Drawdown: {:.2%}", results.max_drawdown)
            logger.info("Total Return: {:.2%}", results.total_return)
            logger.info("=" * 80)
            return
        except ImportError as e:
            logger.error("Backtesting system not available: {}", e)
            logger.info("Run: python validate_integrations.py to check integration status")
            sys.exit(1)
    
    # Run orchestrator mode if requested
    if args.orchestrator or args.enable_scanners or args.advanced_exits or args.adaptive:
        logger.info("=" * 80)
        logger.info("ALPHAALGO - INTEGRATED SYSTEMS MODE")
        logger.info("=" * 80)
        logger.info("Enabled systems:")
        if args.orchestrator:
            logger.info("  ✓ Master Orchestrator")
        if args.enable_scanners:
            logger.info("  ✓ Opportunity Scanners")
        if args.advanced_exits:
            logger.info("  ✓ Advanced Exit Strategies")
        if args.adaptive:
            logger.info("  ✓ Adaptive Systems")
        logger.info("=" * 80)
        
        try:
            from trading_bot import (
                MasterOrchestrator,
                TradingMode,
                MarketInefficiencyScanner,
                MomentumBurstDetector,
                ExitSignalGenerator,
                ProfitMaximizer,
                AdaptiveTradingMaster,
                RiskEngine
            )
            
            # Initialize MT5
            mt5i = MT5Interface()
            symbol = args.symbol or "EURUSD"
            
            # Map trading mode
            mode_map = {
                'aggressive': TradingMode.AGGRESSIVE,
                'balanced': TradingMode.BALANCED,
                'conservative': TradingMode.CONSERVATIVE,
                'defensive': TradingMode.DEFENSIVE,
                'scalping': TradingMode.SCALPING,
                'swing': TradingMode.SWING,
                'position': TradingMode.POSITION
            }
            trading_mode = mode_map.get(args.trading_mode, TradingMode.BALANCED)
            
            # Initialize opportunity scanners if enabled
            scanners = []
            if args.enable_scanners:
                logger.info("Initializing opportunity scanners...")
                scanners.append(MarketInefficiencyScanner())
                scanners.append(MomentumBurstDetector())
                logger.info("Initialized {} scanners", len(scanners))
            
            # Initialize exit strategies if enabled
            exit_generator = None
            if args.advanced_exits:
                logger.info("Initializing advanced exit strategies...")
                exit_generator = ExitSignalGenerator()
                # Add profit maximizer strategy
                exit_generator.add_strategy(ProfitMaximizer())
                logger.info("Exit strategies initialized")
            
            # Initialize adaptive systems if enabled
            adaptive_master = None
            if args.adaptive:
                logger.info("Initializing adaptive systems...")
                # Create default config for adaptive master
                adaptive_config = {
                    'regime_detection': {},
                    'strategy_selection': {},
                    'parameter_optimization': {},
                    'self_improvement': {}
                }
                adaptive_master = AdaptiveTradingMaster(config=adaptive_config)
                logger.info("Adaptive systems initialized")
            
            # Initialize risk engine
            risk_engine = RiskEngine()
            
            # Initialize orchestrator
            logger.info("Initializing master orchestrator...")
            orchestrator = MasterOrchestrator(
                mt5_interface=mt5i,
                symbol=symbol,
                trading_mode=trading_mode,
                opportunity_scanners=scanners if scanners else None,
                exit_generator=exit_generator,
                adaptive_master=adaptive_master,
                risk_engine=risk_engine
            )
            
            logger.info("=" * 80)
            logger.info("All systems initialized successfully!")
            logger.info("Starting integrated trading system...")
            logger.info("Symbol: {}, Mode: {}, Trading Mode: {}", symbol, args.mode, trading_mode.value)
            logger.info("=" * 80)
            
            # Run the orchestrator
            await orchestrator.run()
            return
            
        except ImportError as e:
            logger.error("Integrated systems not available: {}", e)
            logger.info("Run: python validate_integrations.py to check integration status")
            logger.info("Falling back to traditional mode...")
            # Fall through to traditional mode below

    # Trading parameters
    symbol = args.symbol or "EURUSD"  # Default to EURUSD if not specified
    mode = args.mode
    timeframe = args.timeframe
    bars = args.bars
    
    # Additional symbols for multi-symbol trading
    additional_symbols = []
    if args.additional_symbols:
        additional_symbols = [s.strip() for s in args.additional_symbols.split(',') if s.strip()]
        logger.info(f"Additional trading symbols: {', '.join(additional_symbols)}")
    
    # Initialize trader
    if additional_symbols:
        # Multi-symbol trading
        trader = MultiSymbolTrader(
            primary_symbol=symbol,
            additional_symbols=additional_symbols,
            timeframe=timeframe,
            bars=bars,
            manage_correlations=args.manage_correlations,
            max_correlated_exposure=args.max_correlated_exposure
        )
    else:
        # Single-symbol trading
        try:
            with MT5Interface() as mt5i:
                # MLStrategyEngine accepts: use_price_prediction, use_pattern_recognition, use_sentiment
                strategy_engine = MLStrategyEngine(
                    mt5i,
                    symbol=symbol,
                    use_price_prediction=True,
                    use_pattern_recognition=True,
                    use_sentiment=args.sentiment_analysis
                ) if args.use_ml else StrategyEngine(mt5i, symbol=symbol)
                
                risk_manager = RiskManager(mt5i)
                
                executor = _select_executor(mt5i, risk_manager, mode, args.execution_algo)
                trader = {
                    'strategy': strategy_engine,
                    'risk': risk_manager,
                    'executor': executor
                }
        except Exception as e:
            logger.error("Error initializing single-symbol trader: {}", e)
            raise  # Re-raise to prevent continuing with uninitialized variables
    
    log_level = args.log_level
    enable_profiling = args.profile
    use_ml = args.use_ml
    use_transformer = args.use_transformer
    use_rl = args.use_rl
    market_regime = args.market_regime
    execution_algo = args.execution_algo
    track_emotions = args.track_emotions
    sentiment_analysis = args.sentiment_analysis
    order_flow = args.order_flow
    quantum_blockchain = args.quantum_blockchain
    adaptive_mode = args.adaptive_mode
    self_improve = args.self_improve
    internet_access = args.internet_access
    api_source = args.api_source
    websocket_feed = args.websocket_feed
    news_scraping = args.news_scraping
    cache_dir = args.cache_dir
    api_keys_file = args.api_keys_file
    news_data_dir = args.news_data_dir
    
    # Initialize intelligence components
    news_pipeline = None
    strategy_researcher = None
    fundamental_analyzer = None
    connectivity_components = {}
    
    # Note: API keys should now be loaded from environment variables
    # news_api_key and fred_api_key arguments were removed for security
    news_api_key = os.getenv('NEWS_API_KEY')
    fred_api_key = os.getenv('FRED_API_KEY')
    
    # Initialize connectivity if needed
    if internet_access:
        logger.info("Initializing internet connectivity components...")
        connectivity_components = _initialize_connectivity(
            api_source, websocket_feed, news_scraping, cache_dir, api_keys_file
        )
    
    # Initialize news pipeline if sentiment analysis enabled
    if sentiment_analysis and (internet_access or news_api_key):
        logger.info("Initializing news pipeline for sentiment analysis...")
        try:
            news_pipeline = NewsPipeline(
                newsapi_key=news_api_key,
                data_dir=news_data_dir
            )
        except Exception as e:
            logger.warning(f"Could not initialize news pipeline: {e}")
    
    # Initialize strategy researcher if enabled
    if args.strategy_research:
        logger.info("Initializing strategy researcher...")
        try:
            strategy_researcher = StrategyResearcher(
                db_path=args.research_data_dir
            )
        except Exception as e:
            logger.warning(f"Could not initialize strategy researcher: {e}")
    
    # Initialize fundamental analyzer if enabled
    if args.fundamental_analysis:
        logger.info("Initializing fundamental analyzer...")
        try:
            fundamental_analyzer = FundamentalAnalyzer(
                fred_api_key=fred_api_key,
                db_path=args.research_data_dir
            )
        except Exception as e:
            logger.warning(f"Could not initialize fundamental analyzer: {e}")
    
    # ------------------------------------------------------------------
    # Main trading loop with graceful shutdown support
    # ------------------------------------------------------------------
    
    # Graceful shutdown flag
    shutdown_requested = False
    
    def handle_shutdown_signal(signum, frame):
        nonlocal shutdown_requested
        logger.warning(f"Shutdown signal {signum} received")
        shutdown_requested = True
    
    import signal
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    # Start recursive self-improvement background loop
    if recursive_system:
        try:
            await recursive_system.start()
            logger.info("Recursive self-improvement background loop STARTED")
        except Exception as e:
            logger.error(f"Failed to start recursive improvement loop: {e}")
    
    try:
        df = None
        with MT5Interface() as mt5i:
            while not shutdown_requested:
                try:
                    if isinstance(trader, MultiSymbolTrader):
                        # Multi-symbol trading
                        await trader.process_symbols()
                    else:
                        # Single-symbol trading
                        # Refresh df (market data) each iteration
                        rates = mt5i.get_rates(symbol, timeframe=timeframe, count=bars)
                        if len(rates) == 0:
                            logger.error("No market data downloaded. Abort.")
                            await asyncio.sleep(5)
                            continue
                        data = [
                            {
                                "time": r["time"],
                                "open": r["open"],
                                "high": r["high"],
                                "low": r["low"],
                                "close": r["close"],
                                "volume": r["tick_volume"],
                                "real_volume": r["real_volume"],
                            }
                            for r in rates
                        ]
                        df = pd.DataFrame(data)
                        df.set_index("time", inplace=True)
                        if hasattr(trader['strategy'], 'generate_signals'):
                            signals = await trader['strategy'].generate_signals()
                        else:
                            signals = trader['strategy'].analyse(df)
                        
                        # --- Extended systems: pre-trade processing ---
                        last_close = float(df['close'].iloc[-1]) if 'close' in df.columns else 0.0
                        market_snapshot = {
                            'symbol': symbol, 'price': last_close,
                            'open': float(df['open'].iloc[-1]) if 'open' in df.columns else last_close,
                            'high': float(df['high'].iloc[-1]) if 'high' in df.columns else last_close,
                            'low': float(df['low'].iloc[-1]) if 'low' in df.columns else last_close,
                            'close': last_close,
                            'volume': float(df['tick_volume'].iloc[-1]) if 'tick_volume' in df.columns else 0.0,
                            'timestamp': str(df.index[-1]) if len(df) > 0 else '',
                            'sma_20': float(df['close'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else last_close,
                            'sma_50': float(df['close'].rolling(50).mean().iloc[-1]) if len(df) >= 50 else last_close,
                            'macd': 0.0, 'rsi': 50.0, 'volatility': float(df['close'].pct_change().std()) if len(df) > 2 else 0.01,
                        }
                        
                        # Multi-agent consensus
                        if 'agent_coordinator' in extended_systems:
                            try:
                                coord = extended_systems['agent_coordinator']
                                proposals = coord.get_proposals(market_snapshot)
                                agent_decision = coord.aggregate_decisions(proposals)
                                market_snapshot['agent_consensus'] = agent_decision
                                logger.debug(f"Agent consensus: {agent_decision.get('action', 'HOLD')}")
                            except Exception as e:
                                logger.warning(f"Agent coordinator error: {e}")
                        
                        # Neuro-symbolic reasoning
                        if 'reasoner' in extended_systems:
                            try:
                                reasoning_result = extended_systems['reasoner'].reason_about_trade(market_snapshot)
                                if reasoning_result:
                                    market_snapshot['reasoning'] = reasoning_result
                            except Exception as e:
                                logger.warning(f"Reasoning error: {e}")
                        
                        # Superintelligence processing
                        if 'superintelligence' in extended_systems:
                            try:
                                si_result = extended_systems['superintelligence'].process(market_snapshot)
                                if si_result:
                                    market_snapshot['superintelligence'] = si_result
                            except Exception as e:
                                logger.warning(f"Superintelligence error: {e}")
                        
                        # Regime strategy engine
                        if 'regime_engine' in extended_systems:
                            try:
                                regime_result = extended_systems['regime_engine'].process(market_snapshot)
                                if regime_result:
                                    market_snapshot['regime'] = regime_result
                            except Exception as e:
                                logger.warning(f"Regime engine error: {e}")
                        
                        # Red Team / Blue Team adversarial validation
                        if 'red_team_blue_team' in extended_systems:
                            try:
                                rtbt_result = extended_systems['red_team_blue_team'].process(market_snapshot)
                                if rtbt_result:
                                    market_snapshot['adversarial_validation'] = rtbt_result
                            except Exception as e:
                                logger.warning(f"Red Team/Blue Team error: {e}")
                        
                        # Archive orchestrator pre-trade (126 modules)
                        if 'archive_orchestrator' in extended_systems:
                            try:
                                market_snapshot = extended_systems['archive_orchestrator'].pre_trade_process(market_snapshot)
                            except Exception as e:
                                logger.warning(f"Archive orchestrator pre-trade error: {e}")
                        
                        # --- Cognitive Architecture: 10-layer decision pipeline ---
                        cognitive_decision = None
                        if 'cognitive_core' in extended_systems:
                            try:
                                cognitive_decision = extended_systems['cognitive_core'].make_decision(market_snapshot)
                                if cognitive_decision:
                                    market_snapshot['cognitive_decision'] = cognitive_decision
                                    logger.debug(f"Cognitive decision: {getattr(cognitive_decision, 'action', 'N/A')} "
                                               f"confidence={getattr(cognitive_decision, 'confidence', 0):.2f}")
                            except Exception as e:
                                logger.warning(f"Cognitive architecture error: {e}")
                        
                        # --- Recursive Self-Improvement: pre-trade optimization ---
                        if 'recursive_improvement' in extended_systems:
                            try:
                                ri = extended_systems['recursive_improvement']
                                # Feed market data for strategy evolution
                                if hasattr(ri, 'strategy') and hasattr(ri.strategy, 'evaluate_signals'):
                                    ri.strategy.evaluate_signals(signals, market_snapshot)
                                # Feed market data for risk optimization
                                if hasattr(ri, 'risk') and hasattr(ri.risk, 'optimize_parameters'):
                                    ri.risk.optimize_parameters(market_snapshot)
                            except Exception as e:
                                logger.warning(f"Recursive improvement pre-trade error: {e}")
                        
                        # --- Trade Triage: analyze signal quality ---
                        if 'trade_triage' in extended_systems:
                            try:
                                triage = extended_systems['trade_triage']
                                if hasattr(triage, 'evaluate_signal'):
                                    triage_result = triage.evaluate_signal(signals, market_snapshot)
                                    if triage_result:
                                        market_snapshot['triage'] = triage_result
                            except Exception as e:
                                logger.warning(f"Trade triage error: {e}")
                        
                        # --- PROFITABILITY GATE: Only trade if profitable ---
                        # Filter signals through profitability requirements
                        signal_confidence = 0.0
                        if isinstance(signals, dict):
                            signal_confidence = signals.get('confidence', signals.get('strength', 0.5))
                        elif isinstance(signals, list) and signals:
                            signal_confidence = max(
                                safe_get(s, 'confidence', safe_get(s, 'strength', 0.5)) 
                                for s in signals
                            )
                        
                        # Use cognitive decision confidence if available
                        if cognitive_decision and hasattr(cognitive_decision, 'confidence'):
                            signal_confidence = max(signal_confidence, cognitive_decision.confidence)
                        
                        min_confidence = PROFITABILITY_CONFIG['min_confidence']
                        if signal_confidence < min_confidence:
                            logger.debug(f"Signal confidence {signal_confidence:.2f} below threshold {min_confidence} - skipping")
                            await asyncio.sleep(5)
                            continue
                        
                        # --- Position sizing and execution ---
                        position = 0
                        if isinstance(signals, list):
                            for signal in signals:
                                stop_loss_pips = safe_get(signal, 'stop_loss_pips', 20)
                                try:
                                    pos = trader['risk'].calculate_position_size(symbol=symbol, stop_loss_pips=stop_loss_pips)
                                    if hasattr(pos, 'lot') and pos.lot > 0:
                                        position = pos
                                        break
                                    elif pos != 0:
                                        position = pos
                                        break
                                except Exception as e:
                                    logger.warning(f"Skipping signal due to error: {e}")
                        elif isinstance(signals, dict):
                            stop_loss_pips = safe_get(signals, 'stop_loss_pips', 20)
                            try:
                                position = trader['risk'].calculate_position_size(symbol=symbol, stop_loss_pips=stop_loss_pips)
                            except Exception as e:
                                logger.warning(f"Skipping signal due to error: {e}")
                        
                        trade_executed = False
                        trade_direction = 0
                        trade_size = 0
                        
                        if hasattr(position, 'lot') and position.lot > 0:
                            trade_direction = 1 if position.lot > 0 else -1
                            trade_size = abs(position.lot)
                            await trader['executor'].execute_trade(
                                symbol=symbol,
                                direction=trade_direction,
                                size=trade_size
                            )
                            trade_executed = True
                        elif not hasattr(position, 'lot') and position != 0:
                            trade_direction = 1 if position > 0 else -1
                            trade_size = abs(position)
                            await trader['executor'].execute_trade(
                                symbol=symbol,
                                direction=trade_direction,
                                size=trade_size
                            )
                            trade_executed = True
                        
                        # --- Extended systems: post-trade processing ---
                        if trade_executed:
                            # Compliance: record trade
                            if 'compliance' in extended_systems:
                                try:
                                    extended_systems['compliance'].record_trade(
                                        symbol=symbol,
                                        side='BUY' if trade_direction > 0 else 'SELL',
                                        quantity=trade_size,
                                        price=last_close,
                                    )
                                except Exception as e:
                                    logger.warning(f"Compliance record error: {e}")
                            
                            # Trade journal logging
                            if 'trade_journal' in extended_systems:
                                try:
                                    extended_systems['trade_journal'].add_trade(
                                        trade_id=f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                        symbol=symbol,
                                        direction='long' if trade_direction > 0 else 'short',
                                        entry_price=last_close,
                                        exit_price=last_close,
                                        quantity=trade_size,
                                        strategy='main_loop',
                                        reasoning=str(signals)[:500],
                                        market_conditions={'symbol': symbol, 'price': last_close},
                                    )
                                except Exception as e:
                                    logger.warning(f"Trade journal error: {e}")
                            
                            # Learning: record for performance analysis
                            if 'performance_analyzer' in extended_systems:
                                try:
                                    extended_systems['performance_analyzer'].add_trade({
                                        'symbol': symbol,
                                        'direction': trade_direction,
                                        'size': trade_size,
                                        'price': last_close,
                                        'pnl': 0.0,
                                    })
                                except Exception as e:
                                    logger.warning(f"Performance analyzer error: {e}")
                            
                            # Self-optimization feedback
                            if 'self_optimizer' in extended_systems:
                                try:
                                    extended_systems['self_optimizer'].process({
                                        'trade': {'symbol': symbol, 'direction': trade_direction, 'size': trade_size},
                                        'market': market_snapshot,
                                    })
                                except Exception as e:
                                    logger.warning(f"Self-optimizer error: {e}")
                            
                            # Memory systems: store experience
                            if 'memory_systems' in extended_systems:
                                try:
                                    extended_systems['memory_systems'].process({
                                        'trade': {'symbol': symbol, 'direction': trade_direction, 'size': trade_size},
                                        'market': market_snapshot,
                                    })
                                except Exception as e:
                                    logger.warning(f"Memory systems error: {e}")
                        
                        # Self-regulation check
                        if 'self_regulation' in extended_systems:
                            try:
                                extended_systems['self_regulation'].process(market_snapshot)
                            except Exception as e:
                                logger.warning(f"Self-regulation error: {e}")
                        
                        # Archive orchestrator post-trade (126 modules)
                        if trade_executed and 'archive_orchestrator' in extended_systems:
                            try:
                                extended_systems['archive_orchestrator'].post_trade_process({
                                    'symbol': symbol,
                                    'direction': trade_direction,
                                    'size': trade_size,
                                    'price': last_close,
                                    'timestamp': datetime.now().isoformat(),
                                })
                            except Exception as e:
                                logger.warning(f"Archive orchestrator post-trade error: {e}")
                        
                        # --- Recursive Self-Improvement: post-trade learning ---
                        trade_outcome = {
                            'symbol': symbol,
                            'direction': trade_direction,
                            'size': trade_size,
                            'entry_price': last_close,
                            'trade_executed': trade_executed,
                            'signal_confidence': signal_confidence,
                            'market_snapshot': market_snapshot,
                            'timestamp': datetime.now().isoformat(),
                        }
                        
                        if 'recursive_improvement' in extended_systems:
                            try:
                                ri = extended_systems['recursive_improvement']
                                # Feed trade outcome for learning
                                if hasattr(ri, 'core') and hasattr(ri.core, 'record_outcome'):
                                    ri.core.record_outcome(trade_outcome)
                                # Execution optimization learning
                                if hasattr(ri, 'execution') and hasattr(ri.execution, 'record_execution'):
                                    ri.execution.record_execution(trade_outcome)
                                # Meta-recursive control
                                if hasattr(ri, 'meta') and hasattr(ri.meta, 'evaluate_cycle'):
                                    ri.meta.evaluate_cycle(trade_outcome)
                            except Exception as e:
                                logger.warning(f"Recursive improvement post-trade error: {e}")
                        
                        # Continuous learner: learn from trade
                        if 'continuous_learner' in extended_systems:
                            try:
                                extended_systems['continuous_learner'].learn_from_trade(trade_outcome)
                            except Exception as e:
                                logger.warning(f"Continuous learner error: {e}")
                        
                        # Self-improvement engine: analyze for improvements
                        if trade_executed and 'self_improvement_engine' in extended_systems:
                            try:
                                extended_systems['self_improvement_engine'].analyze_trade(trade_outcome)
                            except Exception as e:
                                logger.warning(f"Self-improvement engine error: {e}")
                        
                        # Sleep after processing to avoid infinite loop
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    await asyncio.sleep(5)  # Wait longer on error
                    
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Stop recursive self-improvement
        if recursive_system:
            try:
                await recursive_system.stop()
                logger.info("Recursive self-improvement system stopped")
            except Exception as e:
                logger.warning(f"Error stopping recursive improvement: {e}")
        
        # Cleanup - mt5i handled by context manager
        logger.info("Trading bot shutdown complete")
    
    logger.success("Run finished successfully ☑")


async def _run_adaptive_trading_system(mt5i, symbol, timeframe, df, last_price, mode, execution_algo, 
                               emotional_tracker, self_improve=False, internet_access=False,
                               connectivity_components=None, news_pipeline=None):
    """Run the adaptive trading system with self-improvement capabilities."""
    from trading_bot.adaptive_systems import AdaptiveTradingMaster
    import yaml
    
    # Load adaptive configuration
    try:
        with open('config/adaptive_config.yaml', 'r') as f:
            adaptive_config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Adaptive config not found, using defaults")
        adaptive_config = {}
    
    # Load self-improvement configuration if enabled
    self_improvement_config = None
    if self_improve:
        try:
            with open('config/self_improvement_config.yaml', 'r') as f:
                self_improvement_config = yaml.safe_load(f)
                logger.info("Self-improvement configuration loaded")
        except FileNotFoundError:
            logger.warning("Self-improvement config not found, using defaults")
            self_improvement_config = {}
    
    # Add internet connectivity components to adaptive config if enabled
    if internet_access and connectivity_components:
        if 'connectivity' not in adaptive_config:
            adaptive_config['connectivity'] = {}
        
        # Add connectivity components to config
        adaptive_config['connectivity']['enabled'] = True
        adaptive_config['connectivity']['components'] = {
            k: True for k in connectivity_components.keys()
        }
        
        logger.info("Internet connectivity enabled for adaptive trading system")
    
    # Initialize adaptive trading master with self-improvement if enabled
    master = AdaptiveTradingMaster(adaptive_config, enable_self_improvement=self_improve, 
                                  self_improvement_config=self_improvement_config)
                                  
    # Attach internet connectivity components if available
    if internet_access and connectivity_components:
        for component_name, component in connectivity_components.items():
            if hasattr(master, f"set_{component_name}"):
                getattr(master, f"set_{component_name}")(component)
                logger.info(f"Attached {component_name} to adaptive trading system")
    
    # Start the adaptive system
    await master.start_system()
    
    logger.info("Adaptive Trading Master System initialized and running")
    logger.info("System Status: {}", master.get_system_status())
    
    # Log self-improvement status if enabled
    if self_improve:
        logger.info("Self-improvement system enabled and running")
        if hasattr(master, 'self_improvement_engine'):
            logger.info("Self-improvement engine status: {}", 
                       master.self_improvement_engine.get_stats())
    
    cycle_count = 0
    shutdown_event = asyncio.Event()
    
    def _signal_handler(signum, frame):
        logger.warning(f"Shutdown signal {signum} received in adaptive mode")
        shutdown_event.set()
    
    import signal as _signal
    _signal.signal(_signal.SIGINT, _signal_handler)
    _signal.signal(_signal.SIGTERM, _signal_handler)
    
    try:
        while not shutdown_event.is_set():
            cycle_count += 1
            try:
                # Fetch real market data from MT5
                rates = mt5i.get_rates(symbol, timeframe=timeframe, count=500)
                if not rates or len(rates) == 0:
                    logger.warning("No market data available, retrying in 10s...")
                    await asyncio.sleep(10)
                    continue
                
                current_df = pd.DataFrame([{
                    "time": r["time"] if isinstance(r, dict) else r.time,
                    "open": r["open"] if isinstance(r, dict) else r.open,
                    "high": r["high"] if isinstance(r, dict) else r.high,
                    "low": r["low"] if isinstance(r, dict) else r.low,
                    "close": r["close"] if isinstance(r, dict) else r.close,
                    "volume": r.get("tick_volume", r.get("volume", 0)) if isinstance(r, dict) else getattr(r, 'tick_volume', 0),
                } for r in rates])
                
                current_price = float(current_df['close'].iloc[-1])
                prev_price = float(current_df['close'].iloc[-2]) if len(current_df) > 1 else current_price
                volatility = float(current_df['close'].pct_change().std()) if len(current_df) > 10 else 0.02
                avg_volume = float(current_df['volume'].mean()) if 'volume' in current_df else 1.0
                cur_volume = float(current_df['volume'].iloc[-1]) if 'volume' in current_df else 1.0
                
                # Build real market data dict
                market_data = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'price_data': current_df,
                    'suggested_stop': current_price * (1 - 2 * volatility),
                    'volatility': volatility,
                    'sentiment_score': 0.0,
                    'volume_ratio': cur_volume / avg_volume if avg_volume > 0 else 1.0,
                }
                
                # Add real-time data from internet if available
                if internet_access and connectivity_components:
                    try:
                        if 'api_client' in connectivity_components:
                            api_client = connectivity_components['api_client']
                            if hasattr(api_client, 'get_ticker'):
                                real_time_data = await api_client.get_ticker(symbol)
                                if real_time_data:
                                    market_data['real_time_data'] = real_time_data
                        
                        if 'web_scraper' in connectivity_components and cycle_count % 10 == 0:
                            web_scraper = connectivity_components['web_scraper']
                            if hasattr(web_scraper, 'analyze_market_sentiment'):
                                sentiment_data = await web_scraper.analyze_market_sentiment([symbol])
                                if sentiment_data and symbol in sentiment_data:
                                    market_data['sentiment_score'] = sentiment_data[symbol].get('sentiment', {}).get('compound', 0.0)
                        
                        if news_pipeline and cycle_count % 10 == 0:
                            if hasattr(news_pipeline, 'generate_signals'):
                                news_signals = await news_pipeline.generate_signals([symbol])
                                if news_signals:
                                    market_data['news_signals'] = news_signals
                    except Exception as e:
                        logger.warning(f"Error retrieving internet data: {e}")
                
                # Make trading decision using adaptive system
                decision = await master.make_trading_decision(market_data)
                
                logger.info(f"Cycle {cycle_count}: {decision.action} {decision.symbol} @ {current_price:.5f} - "
                           f"Confidence: {decision.confidence:.2f}, "
                           f"Strategy: {decision.strategy.value}, "
                           f"Regime: {decision.regime.value}")
                
                # Record outcome for learning (use actual price change as proxy)
                price_change = (current_price - prev_price) / prev_price if prev_price > 0 else 0
                outcome = {
                    'pnl': price_change * 10000,  # Convert to pips-like metric
                    'duration_minutes': 5,
                    'max_drawdown': abs(min(0, price_change)) * 100,
                    'predicted_regime': decision.regime.value,
                    'actual_regime': decision.regime.value,
                }
                master.record_trade_outcome(decision, outcome)
                
                # Display system metrics periodically
                if cycle_count % 10 == 0:
                    status = master.get_system_status()
                    logger.info(f"=== Adaptive System Status (cycle {cycle_count}) ===")
                    logger.info(f"  Total Decisions: {status.get('trade_count', cycle_count)}")
                    if 'system_metrics' in status:
                        for metric, value in status['system_metrics'].items():
                            if isinstance(value, (int, float)):
                                logger.info(f"  {metric}: {value:.3f}")
                
                # Wait before next cycle (5 seconds for responsive trading)
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in adaptive trading cycle {cycle_count}: {e}")
                await asyncio.sleep(10)
    
    finally:
        # Stop the adaptive system
        await master.stop_system()
        logger.info("Adaptive Trading Master System stopped")
        
        # Close internet connectivity components
        if internet_access and connectivity_components:
            logger.info("Closing internet connectivity components...")
            
            # Close API clients
            for component_name, component in connectivity_components.items():
                if hasattr(component, 'close'):
                    await component.close()
                elif hasattr(component, 'async_close'):
                    await component.async_close()
            
            logger.info("Internet connectivity components closed")


def _run_performance_test(mt5i, symbol, timeframe, bars, use_ml=False):
    """Run performance tests on key components including quantum blockchain features."""
    # Get data once for all tests
    rates = mt5i.get_rates(symbol, timeframe=timeframe, count=bars)
    df = pd.DataFrame(
        [
            {
                "time": r.time,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.tick_volume,
            }
            for r in rates
        ]
    )
    
    from trading_bot.analysis.market_structure import MarketStructureAnalyzer
    from trading_bot.analysis.liquidity import LiquidityAnalyzer
    from trading_bot.analysis.fvg import FVGDetector
    from trading_bot.analysis.order_block import OrderBlockDetector
    from trading_bot.analysis.wyckoff import WyckoffAnalyzer
    from trading_bot.analysis.price_action import PriceActionAnalyzer
    from trading_bot.analysis.order_flow import OrderFlowAnalyzer
    from trading_bot.ml import PricePredictor, StrategyOptimizer, SentimentAnalyzer, TransformerModel, PPOAgent, MarketRegimeClassifier
    
    # Import quantum blockchain features
    try:
        from trading_bot.advanced_features.quantum_computing import QuantumPortfolioOptimizer, QuantumRiskParity, QuantumNashEquilibrium
        from trading_bot.advanced_features.blockchain_validation import BlockchainPredictionSystem, TradingPredictionValidator
        quantum_available = True
        logger.info("Quantum computing and blockchain validation modules loaded successfully")
    except ImportError as e:
        quantum_available = False
        logger.warning("Quantum blockchain features not available: %s", e)
    
    # Test each component separately
    with contextlib.nullcontext():  # MarketStructureAnalyzer
        msa = MarketStructureAnalyzer()
        msa.detect_structure(df)
    
    with contextlib.nullcontext():  # LiquidityAnalyzer
        lqa = LiquidityAnalyzer()
        buy_pools, sell_pools = lqa.find_equal_highs_lows(df)
        lqa.detect_grabs(df, [*buy_pools, *sell_pools])
    
    with contextlib.nullcontext():  # FVGDetector
        fvg = FVGDetector()
        fvg.find_gaps(df)
        fvg.active_gaps(df)
    
    with contextlib.nullcontext():  # OrderBlockDetector
        obd = OrderBlockDetector()
        structure_events = msa.detect_structure(df)
        order_blocks = obd.from_bos(df, structure_events)
        obd.active_blocks(df, order_blocks)
    
    with contextlib.nullcontext():  # WyckoffAnalyzer
        wyckoff = WyckoffAnalyzer()
        wyckoff.detect_phase(df)
    
    with contextlib.nullcontext():  # PriceActionAnalyzer
        pa = PriceActionAnalyzer()
        pa.analyze_price_action(df)
    
    with contextlib.nullcontext():  # OrderFlowAnalyzer
        of = OrderFlowAnalyzer()
        of.analyze_order_flow(df)
    
    # Test full strategy engine
    with contextlib.nullcontext():  # StrategyEngine-full
        strat = StrategyEngine(mt5i, symbol=symbol)
        strat.analyse(data=df)
    
    # Test ML components if enabled
    if use_ml:
        with contextlib.nullcontext():  # PricePredictor
            predictor = PricePredictor()
            predictor.prepare_features(df)
            predictor.predict(df)
        
        with contextlib.nullcontext():  # TransformerModel
            transformer = TransformerModel()
            transformer.prepare_data(df)
            transformer.predict(df)
        
        with contextlib.nullcontext():  # PPOAgent
            ppo = PPOAgent()
            ppo.preprocess_state(df)
            ppo.act(df.iloc[-1])
        
        with contextlib.nullcontext():  # MarketRegimeClassifier
            regime = MarketRegimeClassifier()
            regime.classify(df)
        
        with contextlib.nullcontext():  # MLStrategyEngine-full
            ml_config = {
                "use_transformer": True,
                "use_rl": True,
                "use_sentiment": True,
                "market_regime": True,
                "order_flow": True
            }
            ml_strat = MLStrategyEngine(mt5i, symbol=symbol)
            ml_strat.analyse(df)
    
    # Test quantum blockchain features if available
    if quantum_available:
        logger.info("Testing quantum computing and blockchain validation features...")
        
        # Test quantum portfolio optimization
        with contextlib.nullcontext():  # QuantumPortfolioOptimizer
            try:
                quantum_optimizer = QuantumPortfolioOptimizer()
                # Create sample returns data from price data
                returns = df['close'].pct_change().dropna().values[-50:]  # Last 50 returns
                if len(returns) >= 10:
                    result = quantum_optimizer.optimize_portfolio(returns[:10])  # Use first 10 assets worth of data
                    logger.info("Quantum portfolio optimization completed - Sharpe: {:.4f}", result.sharpe_ratio)
            except Exception as e:
                logger.warning("Quantum portfolio optimization test failed: {}", e)
        
        # Test quantum risk parity
        with contextlib.nullcontext():  # QuantumRiskParity
            try:
                risk_parity = QuantumRiskParity()
                returns = df['close'].pct_change().dropna().values[-50:]
                if len(returns) >= 5:
                    result = risk_parity.optimize_risk_parity(returns[:5])
                    logger.info("Quantum risk parity completed - Risk level: {:.4f}", result.risk_level)
            except Exception as e:
                logger.warning("Quantum risk parity test failed: {}", e)
        
        # Test quantum Nash equilibrium
        with contextlib.nullcontext():  # QuantumNashEquilibrium
            try:
                nash_eq = QuantumNashEquilibrium()
                # Create sample payoff matrix
                payoff_matrix = np.random.rand(3, 3) * 100
                equilibrium = nash_eq.solve(payoff_matrix)
                logger.info("Quantum Nash equilibrium completed - Stability: {:.4f}", equilibrium.stability_score)
            except Exception as e:
                logger.warning("Quantum Nash equilibrium test failed: {}", e)
        
        # Test blockchain prediction system
        with contextlib.nullcontext():  # BlockchainPredictionSystem
            try:
                blockchain_system = BlockchainPredictionSystem()
                # Create sample predictions
                predictions = [
                    {"symbol": symbol, "prediction": "BUY", "confidence": 0.85, "target_price": df['close'].iloc[-1] * 1.02},
                    {"symbol": symbol, "prediction": "SELL", "confidence": 0.75, "target_price": df['close'].iloc[-1] * 0.98}
                ]
                
                for pred in predictions:
                    blockchain_system.record_prediction(pred)
                
                # Validate predictions
                validator = TradingPredictionValidator(blockchain_system)
                validation_result = validator.validate_predictions(df)
                logger.info("Blockchain validation completed - Accuracy: {:.2f}%", 
                          validation_result.get('accuracy_rate', 0) * 100)
            except Exception as e:
                logger.warning("Blockchain prediction system test failed: {}", e)
        
        logger.info("Quantum blockchain performance tests completed")
    
    logger.info("Performance profiling complete")


def _initialize_connectivity(api_source, websocket_feed, news_scraping, cache_dir, api_keys_file):
    """Initialize internet connectivity components."""
    components = {}
    
    # Initialize cache manager
    try:
        from trading_bot.connectivity.cache_manager import CacheManager
        components['cache_manager'] = CacheManager(cache_dir=cache_dir or "cache")
        logger.info("Cache manager initialized")
    except Exception as e:
        logger.warning(f"Could not initialize cache manager: {e}")
    
    # Initialize API client based on source
    if api_source:
        try:
            from trading_bot.connectivity.api_client import APIClient
            api_urls = {
                'yahoo': 'https://query1.finance.yahoo.com',
                'alphavantage': 'https://www.alphavantage.co',
                'binance': 'https://api.binance.com',
                'coinbase': 'https://api.coinbase.com',
            }
            base_url = api_urls.get(api_source, api_urls.get('yahoo'))
            components['api_client'] = APIClient(
                base_url=base_url,
                api_name=api_source,
            )
            logger.info(f"API client initialized for {api_source}")
        except Exception as e:
            logger.warning(f"Could not initialize API client: {e}")
    
    # Initialize websocket client for real-time feeds
    if websocket_feed:
        try:
            from trading_bot.connectivity.websocket_client import WebsocketClient
            ws_urls = {
                'binance': 'wss://stream.binance.com:9443/ws',
                'coinbase': 'wss://ws-feed.exchange.coinbase.com',
            }
            ws_url = ws_urls.get(websocket_feed, ws_urls.get('binance'))
            components['websocket_client'] = WebsocketClient(url=ws_url)
            logger.info(f"WebSocket client initialized for {websocket_feed}")
        except Exception as e:
            logger.warning(f"Could not initialize WebSocket client: {e}")
    
    # Initialize web scraper for news
    if news_scraping:
        try:
            from trading_bot.connectivity.web_scraper import WebScraper
            components['web_scraper'] = WebScraper()
            logger.info("Web scraper initialized for news scraping")
        except Exception as e:
            logger.warning(f"Could not initialize web scraper: {e}")
    
    logger.info(f"Connectivity initialized with {len(components)} components: {list(components.keys())}")
    return components

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    return parse_args(argv)

def _select_executor(mt5i, risk_manager, mode, execution_algo, emotional_tracker=None):
    """Select appropriate executor based on mode and algorithm."""
    if mode == "paper":
        base_executor = PaperExecutor(mt5i, risk_manager)
    elif mode == "live":
        base_executor = LiveExecutor(mt5i, risk_manager)
    elif mode == "smoke":
        # Smoke test mode - use paper executor for connectivity testing only
        logger.info("Using smoke test mode - paper executor for connectivity testing only")
        base_executor = PaperExecutor(mt5i, risk_manager)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    # Apply execution algorithm wrapper if specified
    if execution_algo == "twap":
        logger.info("Using TWAP execution algorithm")
        return TWAPExecutor(base_executor)
    elif execution_algo == "vwap":
        logger.info("Using VWAP execution algorithm")
        return VWAPExecutor(base_executor)
    elif execution_algo == "smart":
        logger.info("Using Smart Order Router (standalone mode)")
        # SmartOrderRouter is standalone, doesn't wrap an executor
        # Return base executor for now (SmartOrderRouter needs separate integration)
        return base_executor
    else:
        logger.info("Using default execution")
        return base_executor

def _display_performance_summary(perf, include_emotions=False):
    logger.info("Performance Summary:")
    logger.info("  Trades: {}  Win Rate: {}%", perf["trades"], perf["win_rate"])
    logger.info("  Net P/L: ${:.2f}  Expectancy: ${:.2f}/trade", 
              perf["net_profit"], perf["expectancy"])
    logger.info("  Max Drawdown: ${:.2f}", perf["max_drawdown"])
    
    # Display ML model metrics if available
    if "ml_metrics" in perf:
        logger.info("ML Model Performance:")
        ml_metrics = perf["ml_metrics"]
        
        if "prediction_accuracy" in ml_metrics:
            logger.info("  Prediction Accuracy: {:.2f}%", ml_metrics["prediction_accuracy"])
            
        if "transformer" in ml_metrics:
            t_metrics = ml_metrics["transformer"]
            logger.info("  Transformer Model:")
            logger.info("    RMSE: {:.4f}  MAE: {:.4f}", t_metrics.get("rmse", 0), t_metrics.get("mae", 0))
            logger.info("    Direction Accuracy: {:.2f}%", t_metrics.get("direction_accuracy", 0))
        
        if "rl_agent" in ml_metrics:
            rl_metrics = ml_metrics["rl_agent"]
            logger.info("  RL Agent (PPO):")
            logger.info("    Mean Reward: {:.2f}  Sharpe: {:.2f}", 
                      rl_metrics.get("mean_reward", 0), rl_metrics.get("sharpe", 0))
            logger.info("    Policy Loss: {:.4f}  Value Loss: {:.4f}", 
                      rl_metrics.get("policy_loss", 0), rl_metrics.get("value_loss", 0))
    
    # Display emotional insights if available
    if include_emotions and "emotional_impact" in perf:
        logger.info("Emotional Impact Analysis:")
        for emotion, impact in perf["emotional_impact"].items():
            if isinstance(impact, dict) and "correlation" in impact:
                logger.info("  {}: {:.2f} correlation with performance", 
                          emotion.capitalize(), impact["correlation"])
        
        if "recommendations" in perf and perf["recommendations"]:
            logger.info("Recommendations:")
            for i, rec in enumerate(perf["recommendations"], 1):
                logger.info("  {}. {}", i, rec)
                
    # Display market regime information if available
    if "market_regime" in perf:
        logger.info("Market Regime Analysis:")
        logger.info("  Current Regime: {}", perf["market_regime"].get("current", "Unknown"))
        logger.info("  Regime Confidence: {:.2f}%", perf["market_regime"].get("confidence", 0) * 100)
        if "transition_probability" in perf["market_regime"]:
            logger.info("  Regime Transition Probability: {:.2f}%", 
                      perf["market_regime"]["transition_probability"] * 100)


def _initialize_connectivity(api_source, websocket_feed, news_scraping, cache_dir, api_keys_file, news_api_key=None):
    """Initialize internet connectivity components."""
    components = {}
    
    # Initialize auth manager if API keys file is provided
    auth_manager = None
    if api_keys_file and os.path.exists(api_keys_file):
        auth_manager = AuthManager(config_path=api_keys_file)
        components['auth_manager'] = auth_manager
        logger.info(f"Initialized authentication manager with {api_keys_file}")
    
    # Initialize rate limiter
    rate_limiter = create_common_rate_limiter()
    components['rate_limiter'] = rate_limiter
    logger.info("Initialized rate limiter with common API configurations")
    
    # Initialize cache manager if cache directory is provided
    cache_manager = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_manager = CacheManager(
            memory_cache_size=1000,
            disk_cache_dir=cache_dir,
            disk_cache_size_mb=100
        )
        components['cache_manager'] = cache_manager
        logger.info(f"Initialized cache manager with directory: {cache_dir}")
    
    # Initialize API client based on source
    if api_source in ['alphavantage', 'all']:
        alpha_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        if alpha_key or (auth_manager and auth_manager.get_api_key('alpha_vantage')):
            key = alpha_key or auth_manager.get_api_key('alpha_vantage')
            alpha_client = AlphaVantageClient(
                api_key=key,
                rate_limiter=rate_limiter
            )
            components['alpha_vantage_client'] = alpha_client
            if 'api_client' not in components:
                components['api_client'] = alpha_client
            logger.info("Initialized Alpha Vantage API client")
    
    if api_source in ['yahoo', 'all']:
        yahoo_client = YahooFinanceClient(rate_limiter=rate_limiter)
        components['yahoo_finance_client'] = yahoo_client
        if 'api_client' not in components:
            components['api_client'] = yahoo_client
        logger.info("Initialized Yahoo Finance API client")
    
    if api_source in ['binance', 'all']:
        # Initialize Binance API client
        binance_client = APIClient(
            base_url="https://api.binance.com",
            api_name="binance",
            rate_limiter=rate_limiter
        )
        components['binance_client'] = binance_client
        if 'api_client' not in components:
            components['api_client'] = binance_client
        logger.info("Initialized Binance API client")
    
    # Initialize websocket client if enabled
    if websocket_feed:
        binance_ws = BinanceWebsocketClient()
        components['websocket_client'] = binance_ws
        logger.info("Initialized Binance WebSocket client")
    
    # Initialize web scraper if enabled
    if news_scraping:
        web_scraper = FinancialNewsScraper(rate_limiter=rate_limiter)
        components['web_scraper'] = web_scraper
        logger.info("Initialized Financial News Scraper")
    
    logger.info(f"Internet connectivity initialized with {len(components)} components")
    return components


if __name__ == "__main__":
    asyncio.run(main())
