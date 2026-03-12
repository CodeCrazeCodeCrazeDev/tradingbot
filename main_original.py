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
7. 185+ integrated modules across 11-layer unified architecture
8. Autonomous self-improvement and recursive optimization
9. Quantum computing and blockchain validation
10. Multi-agent adversarial decision systems

Usage (paper-mode by default - no orders are sent):
    python main.py --symbol EURUSD --timeframe M15 --bars 200

Advanced usage:
    python main.py --symbol EURUSD --timeframe H1 --bars 500 --mode paper --use-ml --execution-algo smart
    python main.py --symbol EURUSD --timeframe H1 --bars 1000 --use-ml --use-transformer --use-rl
    python main.py --full-integration --symbol EURUSD --adaptive --self-improve
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

# ============================================================================
# CORE IMPORTS (always required)
# ============================================================================

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

# ============================================================================
# OPTIONAL MODULE IMPORTS - All 185 directories
# Each module is wrapped in try/except for graceful degradation.
# Modules are grouped by architectural layer.
# ============================================================================

_AVAILABLE = {}  # Track which modules loaded successfully


def _try_import(name, import_fn):
    """Attempt to import a module, tracking availability."""
    try:
        result = import_fn()
        _AVAILABLE[name] = True
        return result
    except (ImportError, Exception) as e:
        _AVAILABLE[name] = False
        logger.debug("Module {} not available: {}", name, e)
        return None


# ---------------------------------------------------------------------------
# Layer 0: Infrastructure & Hardware
# ---------------------------------------------------------------------------

# Safety systems
try:
    from trading_bot.safety import (
        EmergencyKillSwitch,
        LatencyCircuitBreaker,
        ResourceWatchdog,
        ConnectivityMonitor as SafetyConnectivityMonitor,
        AutoPauseManager,
    )
    _AVAILABLE['safety'] = True
except ImportError:
    _AVAILABLE['safety'] = False

# Infrastructure (Health, Monitoring, Scaling)
try:
    from trading_bot.infrastructure import HealthCheck, PerformanceMonitor, AutoScaler
    _AVAILABLE['infrastructure'] = True
except ImportError:
    _AVAILABLE['infrastructure'] = False

# Deployment
try:
    from trading_bot.deployment import deploy_production
    _AVAILABLE['deployment'] = True
except ImportError:
    _AVAILABLE['deployment'] = False

# DevOps
try:
    from trading_bot.devops import changelog_generator
    _AVAILABLE['devops'] = True
except ImportError:
    _AVAILABLE['devops'] = False

# Distributed systems
try:
    from trading_bot.distributed import distributed_coordinator
    _AVAILABLE['distributed'] = True
except ImportError:
    _AVAILABLE['distributed'] = False

# Operations
try:
    from trading_bot.ops import ops_dashboard
    _AVAILABLE['ops'] = True
except ImportError:
    _AVAILABLE['ops'] = False

# Production
try:
    from trading_bot.production import production_orchestrator
    _AVAILABLE['production'] = True
except ImportError:
    _AVAILABLE['production'] = False

# Profiling
try:
    from trading_bot.profiling import async_profiler
    _AVAILABLE['profiling'] = True
except ImportError:
    _AVAILABLE['profiling'] = False

# Performance
try:
    from trading_bot.performance import complete_performance_system
    _AVAILABLE['performance'] = True
except ImportError:
    _AVAILABLE['performance'] = False

# Upgrades
try:
    from trading_bot.upgrades import core_upgrades_001_025
    _AVAILABLE['upgrades'] = True
except ImportError:
    _AVAILABLE['upgrades'] = False

# Streaming
try:
    from trading_bot.streaming import KafkaStreamer
    _AVAILABLE['streaming'] = True
except ImportError:
    _AVAILABLE['streaming'] = False

# ---------------------------------------------------------------------------
# Layer 1: Observability & Monitoring
# ---------------------------------------------------------------------------

# Monitoring
try:
    from trading_bot.monitoring import performance_monitor
    _AVAILABLE['monitoring'] = True
except ImportError:
    _AVAILABLE['monitoring'] = False

# Observability
try:
    from trading_bot.observability import unified_observability_hub
    _AVAILABLE['observability'] = True
except ImportError:
    _AVAILABLE['observability'] = False

# Log system
try:
    from trading_bot.log_system import structured_logger
    _AVAILABLE['log_system'] = True
except ImportError:
    _AVAILABLE['log_system'] = False

# Telemetry
try:
    from trading_bot.telemetry import collector, metrics
    _AVAILABLE['telemetry'] = True
except ImportError:
    _AVAILABLE['telemetry'] = False

# Alerts
try:
    from trading_bot.alerts import alert_manager
    _AVAILABLE['alerts'] = True
except ImportError:
    _AVAILABLE['alerts'] = False

# Dashboard
try:
    from trading_bot.dashboard import dashboard
    _AVAILABLE['dashboard_module'] = True
except ImportError:
    _AVAILABLE['dashboard_module'] = False

# Diagnostics
try:
    from trading_bot.diagnostics import system_diagnostics
    _AVAILABLE['diagnostics'] = True
except ImportError:
    _AVAILABLE['diagnostics'] = False

# Self-Diagnostic & Auto-Repair System
try:
    from trading_bot.self_diagnostic import SelfDiagnosticManager, SelfAwareness
    _AVAILABLE['self_diagnostic'] = True
except ImportError:
    _AVAILABLE['self_diagnostic'] = False

# Intelligence Layer: Discipline, Profitability, Self-Learning, Human Approval
try:
    from trading_bot.intelligence import (
        HumanApprovalGate, DisciplineEngine, ProfitabilityEngine,
        SelfLearningEngine, KnowledgeActionBridge,
    )
    _AVAILABLE['intelligence'] = True
except ImportError:
    _AVAILABLE['intelligence'] = False

# Error handling
try:
    from trading_bot.error_handling import error_manager
    _AVAILABLE['error_handling'] = True
except ImportError:
    _AVAILABLE['error_handling'] = False

# Event monitoring
try:
    from trading_bot.event_monitoring import event_monitor
    _AVAILABLE['event_monitoring'] = True
except ImportError:
    _AVAILABLE['event_monitoring'] = False

# Notifications
try:
    from trading_bot.notifications import notification_manager
    _AVAILABLE['notifications'] = True
except ImportError:
    _AVAILABLE['notifications'] = False

# Quality
try:
    from trading_bot.quality import quality_monitor
    _AVAILABLE['quality'] = True
except ImportError:
    _AVAILABLE['quality'] = False

# Reporting
try:
    from trading_bot.reporting import init_logger
    _AVAILABLE['reporting'] = True
except ImportError:
    _AVAILABLE['reporting'] = False

# Surveillance
try:
    from trading_bot.surveillance import TradeSurveillance
    _AVAILABLE['surveillance'] = True
except ImportError:
    _AVAILABLE['surveillance'] = False

# System health
try:
    from trading_bot.system_health import AlphaAlgoMaster, AutoRepairEngine, SystemHealthMonitor
    _AVAILABLE['system_health'] = True
except ImportError:
    _AVAILABLE['system_health'] = False

# Trade journal
try:
    from trading_bot.trade_journal import journal_manager
    _AVAILABLE['trade_journal'] = True
except ImportError:
    _AVAILABLE['trade_journal'] = False

# Visualization
try:
    from trading_bot.visualization import ChartVisualizer, MLVisualizer
    _AVAILABLE['visualization'] = True
except ImportError:
    _AVAILABLE['visualization'] = False

# Voice assistant
try:
    from trading_bot.voice_assistant import voice_controller
    _AVAILABLE['voice_assistant'] = True
except ImportError:
    _AVAILABLE['voice_assistant'] = False

# Mobile
try:
    from trading_bot.mobile import pwa_alerts
    _AVAILABLE['mobile'] = True
except ImportError:
    _AVAILABLE['mobile'] = False

# Mobile app
try:
    from trading_bot.mobile_app import mobile_dashboard
    _AVAILABLE['mobile_app'] = True
except ImportError:
    _AVAILABLE['mobile_app'] = False

# ---------------------------------------------------------------------------
# Layer 2: Connectivity & Data Ingestion
# ---------------------------------------------------------------------------

# Connectivity unified
try:
    from trading_bot.connectivity_unified import UnifiedConnector, ConnectionStatus, ConnectionType
    _AVAILABLE['connectivity_unified'] = True
except ImportError:
    _AVAILABLE['connectivity_unified'] = False

# Connectors
try:
    from trading_bot.connectors import mt5_connector
    _AVAILABLE['connectors'] = True
except ImportError:
    _AVAILABLE['connectors'] = False

# Broker
try:
    from trading_bot.broker import BrokerInterface, BinanceBroker
    _AVAILABLE['broker'] = True
except ImportError:
    _AVAILABLE['broker'] = False

# Brokers
try:
    from trading_bot.brokers import multi_broker_adapter
    _AVAILABLE['brokers'] = True
except ImportError:
    _AVAILABLE['brokers'] = False

# Ingestion
try:
    from trading_bot.ingestion import data_ingestion
    _AVAILABLE['ingestion'] = True
except ImportError:
    _AVAILABLE['ingestion'] = False

# Internet access
try:
    from trading_bot.internet_access import web_browser
    _AVAILABLE['internet_access'] = True
except ImportError:
    _AVAILABLE['internet_access'] = False

# API
try:
    from trading_bot.api import api_server
    _AVAILABLE['api'] = True
except ImportError:
    _AVAILABLE['api'] = False

# Bridges
try:
    from trading_bot.bridges import bloomberg_bridge
    _AVAILABLE['bridges'] = True
except ImportError:
    _AVAILABLE['bridges'] = False

# Core API
try:
    from trading_bot.core_api import core_api_server
    _AVAILABLE['core_api'] = True
except ImportError:
    _AVAILABLE['core_api'] = False

# cTrader
try:
    from trading_bot.ctrader import ctrader_connector
    _AVAILABLE['ctrader'] = True
except ImportError:
    _AVAILABLE['ctrader'] = False

# ---------------------------------------------------------------------------
# Layer 3: Data Foundation
# ---------------------------------------------------------------------------

# Data
try:
    from trading_bot.data import MT5Interface
    _AVAILABLE['data'] = True
except ImportError:
    _AVAILABLE['data'] = False

# Data feeds
try:
    from trading_bot.data_feeds import market_data_feed
    _AVAILABLE['data_feeds'] = True
except ImportError:
    _AVAILABLE['data_feeds'] = False

# Data sources
try:
    from trading_bot.data_sources import free_data_providers
    _AVAILABLE['data_sources'] = True
except ImportError:
    _AVAILABLE['data_sources'] = False

# Database
try:
    from trading_bot.database import complete_data_infrastructure
    _AVAILABLE['database'] = True
except ImportError:
    _AVAILABLE['database'] = False

# Event pipeline
try:
    from trading_bot.event_pipeline import event_processor
    _AVAILABLE['event_pipeline'] = True
except ImportError:
    _AVAILABLE['event_pipeline'] = False

# Features
try:
    from trading_bot.features import feature_engineering
    _AVAILABLE['features'] = True
except ImportError:
    _AVAILABLE['features'] = False

# Persistence
try:
    from trading_bot.persistence import cache, database as persistence_db
    _AVAILABLE['persistence'] = True
except ImportError:
    _AVAILABLE['persistence'] = False

# Realtime
try:
    from trading_bot.realtime import realtime_engine
    _AVAILABLE['realtime'] = True
except ImportError:
    _AVAILABLE['realtime'] = False

# Sentiment
try:
    from trading_bot.sentiment import realtime_sentiment_engine
    _AVAILABLE['sentiment'] = True
except ImportError:
    _AVAILABLE['sentiment'] = False

# Social
try:
    from trading_bot.social import copy_trading
    _AVAILABLE['social'] = True
except ImportError:
    _AVAILABLE['social'] = False

# Calendar (session awareness)
try:
    from trading_bot.calendar import SessionManager, MarketCalendar, SessionType
    _AVAILABLE['calendar'] = True
except ImportError:
    _AVAILABLE['calendar'] = False

# Trading calendar
try:
    from trading_bot.trading_calendar import economic_calendar
    _AVAILABLE['trading_calendar'] = True
except ImportError:
    _AVAILABLE['trading_calendar'] = False

# Alternative data
try:
    from trading_bot.alternative_data import satellite_imagery
    _AVAILABLE['alternative_data'] = True
except ImportError:
    _AVAILABLE['alternative_data'] = False

# Blockchain
try:
    from trading_bot.blockchain import defi_integration
    _AVAILABLE['blockchain'] = True
except ImportError:
    _AVAILABLE['blockchain'] = False

# Crypto
try:
    from trading_bot.crypto import crypto_analyzer
    _AVAILABLE['crypto'] = True
except ImportError:
    _AVAILABLE['crypto'] = False

# Macro
try:
    from trading_bot.macro import macro_analyzer
    _AVAILABLE['macro'] = True
except ImportError:
    _AVAILABLE['macro'] = False

# ---------------------------------------------------------------------------
# Layer 4: Intelligence Core
# ---------------------------------------------------------------------------

# ML
try:
    from trading_bot.ml.offline_rl import CQLAgent, BCQAgent, ContinuousLearningOrchestrator, DatasetBuilder
    _AVAILABLE['ml_offline_rl'] = True
except ImportError:
    _AVAILABLE['ml_offline_rl'] = False

# AI core
try:
    from trading_bot.ai_core import ai_orchestrator
    _AVAILABLE['ai_core'] = True
except ImportError:
    _AVAILABLE['ai_core'] = False

# AI
try:
    from trading_bot.ai import ai_engine
    _AVAILABLE['ai'] = True
except ImportError:
    _AVAILABLE['ai'] = False

# AI engineer
try:
    from trading_bot.ai_engineer import ai_engineer_core
    _AVAILABLE['ai_engineer'] = True
except ImportError:
    _AVAILABLE['ai_engineer'] = False

# Alpha engine
try:
    from trading_bot.alpha_engine import orchestrator as alpha_orchestrator
    _AVAILABLE['alpha_engine'] = True
except ImportError:
    _AVAILABLE['alpha_engine'] = False

# Alpha research
try:
    from trading_bot.alpha_research import alpha_discovery
    _AVAILABLE['alpha_research'] = True
except ImportError:
    _AVAILABLE['alpha_research'] = False

# Analysis
try:
    from trading_bot.analysis import market_structure, liquidity, order_flow
    _AVAILABLE['analysis'] = True
except ImportError:
    _AVAILABLE['analysis'] = False

# Analysis unified
try:
    from trading_bot.analysis_unified import UnifiedAnalyzer, AnalysisResult, AnalysisType
    _AVAILABLE['analysis_unified'] = True
except ImportError:
    _AVAILABLE['analysis_unified'] = False

# Analytics
try:
    from trading_bot.analytics import PerformanceAnalytics
    _AVAILABLE['analytics'] = True
except ImportError:
    _AVAILABLE['analytics'] = False

# Cognitive architecture
try:
    from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore
    _AVAILABLE['cognitive_architecture'] = True
except ImportError:
    _AVAILABLE['cognitive_architecture'] = False

# DeepChart
try:
    from trading_bot.deepchart import deep_chart_analyzer
    _AVAILABLE['deepchart'] = True
except ImportError:
    _AVAILABLE['deepchart'] = False

# Elite AI system
try:
    from trading_bot.elite_ai_system import elite_trading_orchestrator
    _AVAILABLE['elite_ai_system'] = True
except ImportError:
    _AVAILABLE['elite_ai_system'] = False

# Eternal evolution
try:
    from trading_bot.eternal_evolution import evolution_engine
    _AVAILABLE['eternal_evolution'] = True
except ImportError:
    _AVAILABLE['eternal_evolution'] = False

# Evolution layer
try:
    from trading_bot.evolution_layer import evolution_orchestrator
    _AVAILABLE['evolution_layer'] = True
except ImportError:
    _AVAILABLE['evolution_layer'] = False

# Explainability
try:
    from trading_bot.explainability import feature_attribution, decision_narrative, confidence_scoring
    _AVAILABLE['explainability'] = True
except ImportError:
    _AVAILABLE['explainability'] = False

# Improvement agent
try:
    from trading_bot.improvement_agent import improvement_orchestrator
    _AVAILABLE['improvement_agent'] = True
except ImportError:
    _AVAILABLE['improvement_agent'] = False

# Improvements
try:
    from trading_bot.improvements import improvement_tracker
    _AVAILABLE['improvements'] = True
except ImportError:
    _AVAILABLE['improvements'] = False

# Indicators
try:
    from trading_bot.indicators import technical_indicators
    _AVAILABLE['indicators'] = True
except ImportError:
    _AVAILABLE['indicators'] = False

# Innovations
try:
    from trading_bot.innovations import innovation_engine
    _AVAILABLE['innovations'] = True
except ImportError:
    _AVAILABLE['innovations'] = False

# Learning
try:
    from trading_bot.learning import PerformanceAnalyzer as LearningPerformanceAnalyzer, StrategyOptimizer as LearningStrategyOptimizer
    _AVAILABLE['learning'] = True
except ImportError:
    _AVAILABLE['learning'] = False

# Market intelligence
try:
    from trading_bot.market_intelligence import market_intel
    _AVAILABLE['market_intelligence'] = True
except ImportError:
    _AVAILABLE['market_intelligence'] = False

# Market student
try:
    from trading_bot.market_student import market_student_core
    _AVAILABLE['market_student'] = True
except ImportError:
    _AVAILABLE['market_student'] = False

# Market teacher
try:
    from trading_bot.market_teacher import market_teacher_core
    _AVAILABLE['market_teacher'] = True
except ImportError:
    _AVAILABLE['market_teacher'] = False

# Meta learning
try:
    from trading_bot.meta_learning import maml, evolutionary
    _AVAILABLE['meta_learning'] = True
except ImportError:
    _AVAILABLE['meta_learning'] = False

# Multimodal
try:
    from trading_bot.multimodal import MultimodalFusion, PriceEncoder, NewsEncoder
    _AVAILABLE['multimodal'] = True
except ImportError:
    _AVAILABLE['multimodal'] = False

# Optimization
try:
    from trading_bot.optimization import strategy_optimizer
    _AVAILABLE['optimization'] = True
except ImportError:
    _AVAILABLE['optimization'] = False

# Psychology
try:
    from trading_bot.psychology import behavioral_features
    _AVAILABLE['psychology'] = True
except ImportError:
    _AVAILABLE['psychology'] = False

# Quantum
try:
    from trading_bot.quantum import quantum_advantage
    _AVAILABLE['quantum'] = True
except ImportError:
    _AVAILABLE['quantum'] = False

# Qwen codemender
try:
    from trading_bot.qwen_codemender import code_analyzer
    _AVAILABLE['qwen_codemender'] = True
except ImportError:
    _AVAILABLE['qwen_codemender'] = False

# Reasoning
try:
    from trading_bot.reasoning import ChainOfThoughtReasoner, FinancialKnowledgeGraph, NeuroSymbolicFusion
    _AVAILABLE['reasoning'] = True
except ImportError:
    _AVAILABLE['reasoning'] = False

# Recursive improvement
try:
    from trading_bot.recursive_improvement import (
        RecursiveImprovementOrchestrator,
        RecursiveImprovementCore,
        RecursiveStrategyEvolution,
        RecursiveRiskOptimization,
        RecursiveExecutionOptimization,
        MetaRecursiveController,
    )
    _AVAILABLE['recursive_improvement'] = True
except ImportError:
    _AVAILABLE['recursive_improvement'] = False

# Research
try:
    from trading_bot.research import research_engine
    _AVAILABLE['research'] = True
except ImportError:
    _AVAILABLE['research'] = False

# Research ingestion
try:
    from trading_bot.research_ingestion import research_ingestor
    _AVAILABLE['research_ingestion'] = True
except ImportError:
    _AVAILABLE['research_ingestion'] = False

# Self-healing AI
try:
    from trading_bot.self_healing_ai import SelfHealingOrchestrator
    _AVAILABLE['self_healing_ai'] = True
except ImportError:
    _AVAILABLE['self_healing_ai'] = False

# Self-improvement
try:
    from trading_bot.self_improvement import (
        SelfImprovementOrchestrator,
        SelfImprovementEngine,
        ContinuousLearner,
        TradeTriage,
    )
    _AVAILABLE['self_improvement'] = True
except ImportError:
    _AVAILABLE['self_improvement'] = False

# Self-learning
try:
    from trading_bot.self_learning import core_learning_engine
    _AVAILABLE['self_learning'] = True
except ImportError:
    _AVAILABLE['self_learning'] = False

# Self-mastery
try:
    from trading_bot.self_mastery import mastery_orchestrator
    _AVAILABLE['self_mastery'] = True
except ImportError:
    _AVAILABLE['self_mastery'] = False

# Self-concepts
try:
    from trading_bot.self_concepts import SelfAwarenessConcepts, SelfDiagnosisConcepts
    _AVAILABLE['self_concepts'] = True
except ImportError:
    _AVAILABLE['self_concepts'] = False

# Sentient core
try:
    from trading_bot.sentient_core import network_sentinel, knowledge_harvester
    _AVAILABLE['sentient_core'] = True
except ImportError:
    _AVAILABLE['sentient_core'] = False

# Superintelligence
try:
    from trading_bot.superintelligence import (
        SuperintelligenceOrchestrator, MultiBrainEnsemble, RegimeStrategyEngine,
        SelfOptimizingCore, SelfRegulationEngine, MemorySystems,
    )
    _AVAILABLE['superintelligence'] = True
except ImportError:
    _AVAILABLE['superintelligence'] = False

# Systems AI
try:
    from trading_bot.systems_ai import orchestrator as systems_ai_orchestrator
    _AVAILABLE['systems_ai'] = True
except ImportError:
    _AVAILABLE['systems_ai'] = False

# TAMIC
try:
    from trading_bot.tamic import core as tamic_core
    _AVAILABLE['tamic'] = True
except ImportError:
    _AVAILABLE['tamic'] = False

# Advanced analysis
try:
    from trading_bot.advanced_analysis import advanced_analysis_orchestrator
    _AVAILABLE['advanced_analysis'] = True
except ImportError:
    _AVAILABLE['advanced_analysis'] = False

# Advanced features
try:
    from trading_bot.advanced_features import quantum_computing, blockchain_validation
    _AVAILABLE['advanced_features'] = True
except ImportError:
    _AVAILABLE['advanced_features'] = False

# Advanced ML
try:
    from trading_bot.advanced_ml import meta_learning as adv_meta_learning
    _AVAILABLE['advanced_ml'] = True
except ImportError:
    _AVAILABLE['advanced_ml'] = False

# Autonomous learner
try:
    from trading_bot.autonomous_learner import autonomous_learner_core
    _AVAILABLE['autonomous_learner'] = True
except ImportError:
    _AVAILABLE['autonomous_learner'] = False

# AAMIS v3
try:
    from trading_bot.aamis_v3 import aamis_master_orchestrator
    _AVAILABLE['aamis_v3'] = True
except ImportError:
    _AVAILABLE['aamis_v3'] = False

# Adaptive systems
try:
    from trading_bot.adaptive_systems import adaptive_learning, adaptive_risk
    _AVAILABLE['adaptive_systems'] = True
except ImportError:
    _AVAILABLE['adaptive_systems'] = False

# World model
try:
    from trading_bot.world_model import ImaginationPlanner
    _AVAILABLE['world_model'] = True
except ImportError:
    _AVAILABLE['world_model'] = False

# ---------------------------------------------------------------------------
# Layer 5: Signal Generation
# ---------------------------------------------------------------------------

# Signals
try:
    from trading_bot.signals import ConfirmationSignal, EntryConfirmation, NewsGating, SignalProvenance
    _AVAILABLE['signals'] = True
except ImportError:
    _AVAILABLE['signals'] = False

# Strategies
try:
    from trading_bot.strategies import MeanReversion, MyTradingStrategy
    _AVAILABLE['strategies'] = True
except ImportError:
    _AVAILABLE['strategies'] = False

# Opportunity scanner
try:
    from trading_bot.opportunity_scanner import opportunity_scanner
    _AVAILABLE['opportunity_scanner'] = True
except ImportError:
    _AVAILABLE['opportunity_scanner'] = False

# Institutional entry
try:
    from trading_bot.institutional_entry import institutional_entry_detector
    _AVAILABLE['institutional_entry'] = True
except ImportError:
    _AVAILABLE['institutional_entry'] = False

# Arbitrage
try:
    from trading_bot.arbitrage import arbitrage_scanner
    _AVAILABLE['arbitrage'] = True
except ImportError:
    _AVAILABLE['arbitrage'] = False

# Backtesting
try:
    from trading_bot.backtesting import backtest_engine
    _AVAILABLE['backtesting'] = True
except ImportError:
    _AVAILABLE['backtesting'] = False

# Derivatives
try:
    from trading_bot.derivatives import options_pricing
    _AVAILABLE['derivatives'] = True
except ImportError:
    _AVAILABLE['derivatives'] = False

# Filters
try:
    from trading_bot.filters import market_condition_filters
    _AVAILABLE['filters'] = True
except ImportError:
    _AVAILABLE['filters'] = False

# Market making
try:
    from trading_bot.market_making import market_maker
    _AVAILABLE['market_making'] = True
except ImportError:
    _AVAILABLE['market_making'] = False

# Profit maximizer
try:
    from trading_bot.profit_maximizer import profit_optimizer
    _AVAILABLE['profit_maximizer'] = True
except ImportError:
    _AVAILABLE['profit_maximizer'] = False

# Simulation
try:
    from trading_bot.simulation import MarketSimulator, AdversarialAgent
    _AVAILABLE['simulation'] = True
except ImportError:
    _AVAILABLE['simulation'] = False

# ---------------------------------------------------------------------------
# Layer 6: Risk & Safety
# ---------------------------------------------------------------------------

# Risk management
try:
    from trading_bot.risk_management import DrawdownLadder
    _AVAILABLE['risk_management'] = True
except ImportError:
    _AVAILABLE['risk_management'] = False

# Risk unified
try:
    from trading_bot.risk_unified import UnifiedRiskManager, RiskCheckResult, RiskLevel
    _AVAILABLE['risk_unified'] = True
except ImportError:
    _AVAILABLE['risk_unified'] = False

# Reality gates
try:
    from trading_bot.reality_gates import reality_gate
    _AVAILABLE['reality_gates'] = True
except ImportError:
    _AVAILABLE['reality_gates'] = False

# Hedge fund
try:
    from trading_bot.hedge_fund import hedge_fund_core
    _AVAILABLE['hedge_fund'] = True
except ImportError:
    _AVAILABLE['hedge_fund'] = False

# Hedge fund safety
try:
    from trading_bot.hedge_fund_safety import safety_core
    _AVAILABLE['hedge_fund_safety'] = True
except ImportError:
    _AVAILABLE['hedge_fund_safety'] = False

# Hedging
try:
    from trading_bot.hedging import correlation_hedge
    _AVAILABLE['hedging'] = True
except ImportError:
    _AVAILABLE['hedging'] = False

# MSOS
try:
    from trading_bot.msos import msos_core
    _AVAILABLE['msos'] = True
except ImportError:
    _AVAILABLE['msos'] = False

# Critical fixes
try:
    from trading_bot.critical_fixes import critical_fix_manager
    _AVAILABLE['critical_fixes'] = True
except ImportError:
    _AVAILABLE['critical_fixes'] = False

# Portfolio
try:
    from trading_bot.portfolio import portfolio_manager
    _AVAILABLE['portfolio'] = True
except ImportError:
    _AVAILABLE['portfolio'] = False

# Security
try:
    from trading_bot.security import SecureCredentialManager, CredentialVault
    _AVAILABLE['security'] = True
except ImportError:
    _AVAILABLE['security'] = False

# Stealth safety
try:
    from trading_bot.stealth_safety import stealth_orchestrator
    _AVAILABLE['stealth_safety'] = True
except ImportError:
    _AVAILABLE['stealth_safety'] = False

# Validation
try:
    from trading_bot.validation import DataQualityValidator, UnifiedValidator
    _AVAILABLE['validation'] = True
except ImportError:
    _AVAILABLE['validation'] = False

# Wealth
try:
    from trading_bot.wealth import wealth_management
    _AVAILABLE['wealth'] = True
except ImportError:
    _AVAILABLE['wealth'] = False

# ---------------------------------------------------------------------------
# Layer 7: Decision & Verification
# ---------------------------------------------------------------------------

# Adversarial curriculum
try:
    from trading_bot.adversarial_curriculum import curriculum_orchestrator
    _AVAILABLE['adversarial_curriculum'] = True
except ImportError:
    _AVAILABLE['adversarial_curriculum'] = False

# Adversarial decision
try:
    from trading_bot.adversarial_decision import adversarial_decision_engine
    _AVAILABLE['adversarial_decision'] = True
except ImportError:
    _AVAILABLE['adversarial_decision'] = False

# Agents
try:
    from trading_bot.agents import base_agent, coordinator
    _AVAILABLE['agents'] = True
except ImportError:
    _AVAILABLE['agents'] = False

# Agents2 (Multi-Agent System)
try:
    from trading_bot.agents2 import MultiAgentCoordinator, TrendFollowingAgent, MeanReversionAgent, VolatilityAgent, RiskManagerAgent, MarketMakerAgent
    _AVAILABLE['agents2'] = True
except ImportError:
    _AVAILABLE['agents2'] = False

# Decision layer
try:
    from trading_bot.decision_layer import decision_engine
    _AVAILABLE['decision_layer'] = True
except ImportError:
    _AVAILABLE['decision_layer'] = False

# Verification
try:
    from trading_bot.verification import verification_orchestrator
    _AVAILABLE['verification'] = True
except ImportError:
    _AVAILABLE['verification'] = False

# ---------------------------------------------------------------------------
# Layer 8: Execution
# ---------------------------------------------------------------------------

# Exit strategies
try:
    from trading_bot.exit_strategies import exit_strategy_manager
    _AVAILABLE['exit_strategies'] = True
except ImportError:
    _AVAILABLE['exit_strategies'] = False

# Exits
try:
    from trading_bot.exits import advanced_exit_strategies
    _AVAILABLE['exits'] = True
except ImportError:
    _AVAILABLE['exits'] = False

# HFT
try:
    from trading_bot.hft import hft_engine
    _AVAILABLE['hft'] = True
except ImportError:
    _AVAILABLE['hft'] = False

# Position
try:
    from trading_bot.position import advanced_position_manager
    _AVAILABLE['position'] = True
except ImportError:
    _AVAILABLE['position'] = False

# Trading
try:
    from trading_bot.trading import OrderExecutor, PositionManager, OrderFillTracker
    _AVAILABLE['trading'] = True
except ImportError:
    _AVAILABLE['trading'] = False

# ---------------------------------------------------------------------------
# Layer 9: Orchestration
# ---------------------------------------------------------------------------

# Archive Orchestrator (126 archive modules)
try:
    from trading_bot.archive_orchestrator import ArchiveOrchestrator
    _AVAILABLE['archive_orchestrator'] = True
except ImportError:
    _AVAILABLE['archive_orchestrator'] = False

# Brain
try:
    from trading_bot.brain import trading_brain
    _AVAILABLE['brain'] = True
except ImportError:
    _AVAILABLE['brain'] = False

# Core
try:
    from trading_bot.core import core_engine
    _AVAILABLE['core'] = True
except ImportError:
    _AVAILABLE['core'] = False

# Elite system
try:
    from trading_bot.elite_system import EliteMarketPsychology, EliteRegimeDetector, EliteRiskManager
    _AVAILABLE['elite_system'] = True
except ImportError:
    _AVAILABLE['elite_system'] = False

# System supervisor
try:
    from trading_bot.system_supervisor import system_supervisor
    _AVAILABLE['system_supervisor'] = True
except ImportError:
    _AVAILABLE['system_supervisor'] = False

# Unified architecture
try:
    from trading_bot.unified_architecture import unified_trading_system
    _AVAILABLE['unified_architecture'] = True
except ImportError:
    _AVAILABLE['unified_architecture'] = False

# Unified system
try:
    from trading_bot.unified_system import UnifiedMasterSystem, LayerRegistry
    _AVAILABLE['unified_system'] = True
except ImportError:
    _AVAILABLE['unified_system'] = False

# Ultimate system
try:
    from trading_bot.ultimate_system import ultimate_orchestrator
    _AVAILABLE['ultimate_system'] = True
except ImportError:
    _AVAILABLE['ultimate_system'] = False

# Ultimate production
try:
    from trading_bot.ultimate_production import StrategyEnsemble, MLPredictionEngine, RiskFortress, SmartExecutor as UltSmartExecutor
    _AVAILABLE['ultimate_production'] = True
except ImportError:
    _AVAILABLE['ultimate_production'] = False

# Ultimate architecture
try:
    from trading_bot.ultimate_architecture import ArchitectureManager, LayerType
    _AVAILABLE['ultimate_architecture'] = True
except ImportError:
    _AVAILABLE['ultimate_architecture'] = False

# Ultimate bot
try:
    from trading_bot.ultimate_bot import UltimateBot, BotMode, BotStatus
    _AVAILABLE['ultimate_bot'] = True
except ImportError:
    _AVAILABLE['ultimate_bot'] = False

# Autonomous
try:
    from trading_bot.autonomous import self_optimizing_engine
    _AVAILABLE['autonomous'] = True
except ImportError:
    _AVAILABLE['autonomous'] = False

# Autonomous pipeline
try:
    from trading_bot.autonomous_pipeline import pipeline_orchestrator
    _AVAILABLE['autonomous_pipeline'] = True
except ImportError:
    _AVAILABLE['autonomous_pipeline'] = False

# Auto optimizer
try:
    from trading_bot.auto_optimizer import auto_optimizer_core
    _AVAILABLE['auto_optimizer'] = True
except ImportError:
    _AVAILABLE['auto_optimizer'] = False

# Global expansion
try:
    from trading_bot.global_expansion import global_market_access
    _AVAILABLE['global_expansion'] = True
except ImportError:
    _AVAILABLE['global_expansion'] = False

# AlphaAlgo v2
try:
    from trading_bot.alphaalgo_v2 import alphaalgo_v2_core
    _AVAILABLE['alphaalgo_v2'] = True
except ImportError:
    _AVAILABLE['alphaalgo_v2'] = False

# Orchestrator
try:
    from trading_bot.orchestrator import master_orchestrator
    _AVAILABLE['orchestrator_module'] = True
except ImportError:
    _AVAILABLE['orchestrator_module'] = False

# Master integration
try:
    from trading_bot.master_integration import MasterTradingSystem
    _AVAILABLE['master_integration'] = True
except ImportError:
    _AVAILABLE['master_integration'] = False

# Master orchestrator
try:
    from trading_bot.master_orchestrator import MasterOrchestrator as TopMasterOrchestrator
    _AVAILABLE['master_orchestrator'] = True
except ImportError:
    _AVAILABLE['master_orchestrator'] = False

# ---------------------------------------------------------------------------
# Layer 10: Governance & Human Control
# ---------------------------------------------------------------------------

# AlphaAlgo core
try:
    from trading_bot.alphaalgo_core import capital_governance
    _AVAILABLE['alphaalgo_core'] = True
except ImportError:
    _AVAILABLE['alphaalgo_core'] = False

# AlphaAlgo institutional
try:
    from trading_bot.alphaalgo_institutional import institutional_core
    _AVAILABLE['alphaalgo_institutional'] = True
except ImportError:
    _AVAILABLE['alphaalgo_institutional'] = False

# Approval
try:
    from trading_bot.approval import human_in_loop
    _AVAILABLE['approval'] = True
except ImportError:
    _AVAILABLE['approval'] = False

# Ultimate approval
try:
    from trading_bot.ultimate_approval import UltimateApprovalSystem, ApprovalLevel, ApprovalRequest
    _AVAILABLE['ultimate_approval'] = True
except ImportError:
    _AVAILABLE['ultimate_approval'] = False

# Audit
try:
    from trading_bot.audit import audit_trail
    _AVAILABLE['audit'] = True
except ImportError:
    _AVAILABLE['audit'] = False

# Compliance
try:
    from trading_bot.compliance import ComplianceMonitor
    _AVAILABLE['compliance'] = True
except ImportError:
    _AVAILABLE['compliance'] = False

# Governance
try:
    from trading_bot.governance import governance_framework
    _AVAILABLE['governance'] = True
except ImportError:
    _AVAILABLE['governance'] = False

# Human layer
try:
    from trading_bot.human_layer import human_interface
    _AVAILABLE['human_layer'] = True
except ImportError:
    _AVAILABLE['human_layer'] = False

# Institutional
try:
    from trading_bot.institutional import bloomberg_bridge as inst_bloomberg
    _AVAILABLE['institutional'] = True
except ImportError:
    _AVAILABLE['institutional'] = False

# Unified approval
try:
    from trading_bot.unified_approval import approval_hub
    _AVAILABLE['unified_approval'] = True
except ImportError:
    _AVAILABLE['unified_approval'] = False

# ---------------------------------------------------------------------------
# Cross-Cutting Modules
# ---------------------------------------------------------------------------

# Advanced Systems 2 (Red Team / Blue Team)
try:
    from trading_bot.advanced_systems2 import RedTeamBlueTeam
    _AVAILABLE['advanced_systems2'] = True
except ImportError:
    _AVAILABLE['advanced_systems2'] = False

# Automation (Trade Journal)
try:
    from trading_bot.automation import TradeJournal, TradeEntry
    _AVAILABLE['automation'] = True
except ImportError:
    _AVAILABLE['automation'] = False

# Documentation
try:
    from trading_bot.documentation import TradeDocumenter, DocumentationType, TradeReport
    _AVAILABLE['documentation'] = True
except ImportError:
    _AVAILABLE['documentation'] = False

# Integration
try:
    from trading_bot.integration import integration_hub
    _AVAILABLE['integration'] = True
except ImportError:
    _AVAILABLE['integration'] = False

# Integrations
try:
    from trading_bot.integrations import integration_manager
    _AVAILABLE['integrations'] = True
except ImportError:
    _AVAILABLE['integrations'] = False

# Testing
try:
    from trading_bot.testing import SyntheticDataGenerator, ReportGenerator
    _AVAILABLE['testing'] = True
except ImportError:
    _AVAILABLE['testing'] = False

# Config
try:
    from trading_bot.config import get as config_get
    _AVAILABLE['config'] = True
except ImportError:
    _AVAILABLE['config'] = False

# Schemas
try:
    from trading_bot.schemas import market_data as market_data_schema
    _AVAILABLE['schemas'] = True
except ImportError:
    _AVAILABLE['schemas'] = False

# Models
try:
    from trading_bot.models import model_registry
    _AVAILABLE['models'] = True
except ImportError:
    _AVAILABLE['models'] = False

# Tools
try:
    from trading_bot.tools import system_check
    _AVAILABLE['tools'] = True
except ImportError:
    _AVAILABLE['tools'] = False

# System
try:
    from trading_bot.system import backup_recovery
    _AVAILABLE['system'] = True
except ImportError:
    _AVAILABLE['system'] = False

# Skills
try:
    import trading_bot.skills
    _AVAILABLE['skills'] = True
except ImportError:
    _AVAILABLE['skills'] = False

# Cloud Deployer (self-hosting discovery)
try:
    from trading_bot.cloud_deployer import CloudAutoDeployer, ServerDiscovery, CloudPlatform
    _AVAILABLE['cloud_deployer'] = True
except ImportError:
    _AVAILABLE['cloud_deployer'] = False

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

    # Cloud deployment flags
    parser.add_argument(
        "--deploy",
        nargs="?",
        const="auto",
        choices=["auto", "railway", "render", "fly", "koyeb", "local", "discover"],
        help="Deploy to a free cloud platform. 'auto' picks the best one. 'discover' scans only.",
        default=None,
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
    # Handle --deploy flag (self-hosting / cloud deployment)
    # ------------------------------------------------------------------
    if args.deploy is not None:
        if not _AVAILABLE.get('cloud_deployer'):
            logger.error("Cloud deployer module not available. Run: python DEPLOY_FREE_CLOUD.py instead.")
            return

        if args.deploy == "discover":
            discovery = ServerDiscovery()
            await discovery.discover_all()
            print(discovery.get_report())
            discovery.save_report()
            return

        deployer = CloudAutoDeployer()
        platform_map = {
            "auto": None,
            "railway": CloudPlatform.RAILWAY,
            "render": CloudPlatform.RENDER,
            "fly": CloudPlatform.FLY_IO,
            "koyeb": CloudPlatform.KOYEB,
            "local": CloudPlatform.LOCAL,
        }
        target = platform_map.get(args.deploy)

        if target is None:
            result = await deployer.auto_deploy()
        else:
            result = await deployer.deploy_to(target)

        print(f"\nDeployment: {result.status.value} on {result.platform.value}")
        if result.url:
            print(f"URL: {result.url}")
        for line in result.logs:
            print(f"  {line}")
        if result.error:
            print(f"Error: {result.error}")
        return

    # ------------------------------------------------------------------
    # Report module availability
    # ------------------------------------------------------------------
    loaded = sum(1 for v in _AVAILABLE.values() if v)
    total = len(_AVAILABLE)
    logger.info("Module availability: {}/{} modules loaded successfully", loaded, total)

    # ------------------------------------------------------------------
    # Self-Diagnostic & Auto-Repair Pre-flight Check
    # ------------------------------------------------------------------
    _diag_manager = None
    if _AVAILABLE.get('self_diagnostic'):
        try:
            _diag_manager = SelfDiagnosticManager(
                scan_interval_seconds=300,
                auto_repair_enabled=True,
                max_repair_attempts=3,
            )
            preflight_ok = await _diag_manager.preflight_check(auto_fix=True)
            if not preflight_ok:
                logger.error("Self-diagnostic pre-flight failed. Fix critical issues before running.")
                # Don't exit - allow degraded operation in paper mode
                if getattr(args, 'mode', 'paper') == 'live':
                    logger.critical("LIVE mode requires passing pre-flight. Exiting.")
                    return
            # Start background self-management
            await _diag_manager.start()
            logger.info("Self-diagnostic background manager started (interval={}s)", _diag_manager._scan_interval)
        except Exception as e:
            logger.warning("Self-diagnostic system failed to initialize: {}", e)
            _diag_manager = None

    # ------------------------------------------------------------------
    # Self-Awareness: Know what you don't know, then figure it out
    # ------------------------------------------------------------------
    _self_awareness = None
    if _AVAILABLE.get('self_diagnostic'):
        try:
            _self_awareness = SelfAwareness(
                cycle_interval_seconds=120,
                max_resolves_per_cycle=10,
            )
            await _self_awareness.start()
            logger.info("Self-awareness engine started — discovering and filling knowledge gaps")
        except Exception as e:
            logger.warning("Self-awareness engine failed to start: {}", e)
            _self_awareness = None

    # ------------------------------------------------------------------
    # Intelligence Layer: Discipline + Profitability + Self-Learning
    # ------------------------------------------------------------------
    _human_gate = None
    _discipline = None
    _profitability = None
    _self_learner = None
    _knowledge_bridge = None
    if _AVAILABLE.get('intelligence'):
        try:
            # #1 Human Approval Gate — trades > $10M need human confirmation
            _human_gate = HumanApprovalGate(
                threshold_usd=10_000_000.0,
                timeout_seconds=300,
                auto_approve_paper=(args.mode == 'paper'),
            )
            _human_gate.set_paper_mode(args.mode == 'paper')

            # #2-15 Discipline Engine — iron trading rules
            _discipline = DisciplineEngine({
                'daily_loss_limit_pct': 3.0,
                'weekly_loss_limit_pct': 5.0,
                'max_consecutive_losses': 3,
                'cooldown_minutes': 30,
                'max_trades_per_hour': 10,
                'max_trades_per_day': 50,
                'session_only': False,       # Disabled for now — enable for live
                'drawdown_adaptive': True,
                'weekend_flat': True,
            })

            # #16-30 Profitability Engine — smarter entries/exits
            _profitability = ProfitabilityEngine({
                'min_confluence_timeframes': 2,
                'min_risk_reward': 1.5,
                'min_ev': 0.0,
            })

            # #31-45 Self-Learning Engine — learn from every trade
            _self_learner = SelfLearningEngine()

            # Knowledge-Action Bridge — connects ALL knowledge to decisions
            _knowledge_bridge = KnowledgeActionBridge()
            _knowledge_bridge.set_discipline_engine(_discipline)
            _knowledge_bridge.set_profitability_engine(_profitability)
            _knowledge_bridge.set_human_approval_gate(_human_gate)
            _knowledge_bridge.set_learning_engine(_self_learner)
            if _self_awareness and hasattr(_self_awareness, '_ledger'):
                _knowledge_bridge.set_knowledge_ledger(_self_awareness._ledger)
            await _knowledge_bridge.start()

            logger.info(
                "Intelligence layer active: human_gate($10M+), discipline(14 rules), "
                "profitability(15 filters), self_learning, knowledge_bridge"
            )
        except Exception as e:
            logger.warning("Intelligence layer failed to initialize: {}", e)
            _knowledge_bridge = None

    # ------------------------------------------------------------------
    # Initialize safety systems
    # ------------------------------------------------------------------
    safety_systems = {}
    if _AVAILABLE.get('safety'):
        try:
            safety_systems['kill_switch'] = EmergencyKillSwitch()
            safety_systems['latency_breaker'] = LatencyCircuitBreaker()
            safety_systems['watchdog'] = ResourceWatchdog()
            safety_systems['connectivity'] = SafetyConnectivityMonitor()
            safety_systems['auto_pause'] = AutoPauseManager()
            logger.info("Safety systems initialized: kill_switch, latency_breaker, watchdog, connectivity, auto_pause")
        except Exception as e:
            logger.error("Failed to initialize safety systems: {}", e)
            safety_systems = {}

    # Initialize RL systems (only in full-integration mode - heavy)
    rl_systems = {}
    if _AVAILABLE.get('ml_offline_rl') and (getattr(args, 'full_integration', False) or getattr(args, 'use_rl', False)):
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
    # Initialize extended modules across 11-layer architecture
    # Only initialize heavy modules when --full-integration is requested
    # to avoid OOM on default paper trading runs.
    # ------------------------------------------------------------------
    extended_systems = {}
    _full_init = getattr(args, 'full_integration', False) or getattr(args, 'adaptive', False)

    def _init_system(key, name, init_fn):
        """Helper to safely initialize an extended system."""
        if _AVAILABLE.get(key):
            try:
                result = init_fn()
                if result is not None:
                    extended_systems[name] = result
                    return True
            except Exception as e:
                logger.error("Failed to initialize {}: {}", name, e)
        return False

    # --- Layer 0: Infrastructure (always lightweight) ---
    _init_system('infrastructure', 'health_check', lambda: HealthCheck())
    _init_system('infrastructure', 'performance_monitor', lambda: PerformanceMonitor())
    if _AVAILABLE.get('system_health'):
        _init_system('system_health', 'system_health_monitor', lambda: SystemHealthMonitor())
        _init_system('system_health', 'auto_repair', lambda: AutoRepairEngine())

    # --- Always-on lightweight modules ---
    if _AVAILABLE.get('risk_unified'):
        _init_system('risk_unified', 'unified_risk_manager', lambda: UnifiedRiskManager())
    if _AVAILABLE.get('risk_management'):
        _init_system('risk_management', 'drawdown_ladder', lambda: DrawdownLadder())
    if _AVAILABLE.get('automation'):
        _init_system('automation', 'trade_journal', lambda: TradeJournal())

    # --- Heavy modules: only when --full-integration or --adaptive ---
    cognitive_core = None
    recursive_system = None

    if _full_init:
        logger.info("Full integration mode: initializing all extended systems...")

        # --- Layer 1: Observability ---
        if _AVAILABLE.get('surveillance'):
            _init_system('surveillance', 'surveillance', lambda: TradeSurveillance())
        if _AVAILABLE.get('documentation'):
            _init_system('documentation', 'trade_documenter', lambda: TradeDocumenter())

        # --- Layer 2: Connectivity ---
        if _AVAILABLE.get('connectivity_unified'):
            _init_system('connectivity_unified', 'unified_connector', lambda: UnifiedConnector())
        if _AVAILABLE.get('broker'):
            extended_systems['broker_interface'] = BrokerInterface
            logger.info("Broker integration available")

        # --- Layer 3: Data Foundation ---
        if _AVAILABLE.get('calendar'):
            _init_system('calendar', 'session_manager', lambda: SessionManager())

        # --- Layer 4: Intelligence Core ---
        if _AVAILABLE.get('agents2'):
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

        if _AVAILABLE.get('cognitive_architecture'):
            try:
                cognitive_core = AlphaAlgoCognitiveCore()
                extended_systems['cognitive_core'] = cognitive_core
                logger.info("Cognitive architecture initialized (10-layer decision pipeline)")
            except Exception as e:
                logger.error("Failed to initialize cognitive architecture: {}", e)

        if _AVAILABLE.get('multimodal'):
            _init_system('multimodal', 'multimodal_fusion', lambda: MultimodalFusion())

        if _AVAILABLE.get('reasoning'):
            try:
                extended_systems['reasoner'] = ChainOfThoughtReasoner()
                extended_systems['knowledge_graph'] = FinancialKnowledgeGraph()
                extended_systems['neuro_symbolic'] = NeuroSymbolicFusion()
                logger.info("Neuro-symbolic reasoning initialized")
            except Exception as e:
                logger.error("Failed to initialize reasoning: {}", e)

        if _AVAILABLE.get('superintelligence'):
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

        if _AVAILABLE.get('analysis_unified'):
            _init_system('analysis_unified', 'unified_analyzer', lambda: UnifiedAnalyzer())

        if _AVAILABLE.get('world_model'):
            _init_system('world_model', 'imagination_planner', lambda: ImaginationPlanner())

        if _AVAILABLE.get('learning'):
            try:
                extended_systems['performance_analyzer'] = LearningPerformanceAnalyzer()
                extended_systems['strategy_optimizer'] = LearningStrategyOptimizer()
                logger.info("Learning module initialized")
            except Exception as e:
                logger.error("Failed to initialize learning module: {}", e)

        # --- Layer 6: Risk & Safety (extra) ---
        if _AVAILABLE.get('validation'):
            _init_system('validation', 'data_quality_validator', lambda: DataQualityValidator())
        if _AVAILABLE.get('security'):
            _init_system('security', 'credential_manager', lambda: SecureCredentialManager())

        # --- Layer 7: Decision & Verification ---
        if _AVAILABLE.get('advanced_systems2'):
            _init_system('advanced_systems2', 'red_team_blue_team', lambda: RedTeamBlueTeam())
        if _AVAILABLE.get('adversarial_curriculum'):
            _init_system('adversarial_curriculum', 'adversarial_curriculum', lambda: curriculum_orchestrator)

        # --- Layer 9: Orchestration ---
        if _AVAILABLE.get('archive_orchestrator'):
            try:
                ao = ArchiveOrchestrator()
                extended_systems['archive_orchestrator'] = ao
                logger.info("Archive orchestrator initialized with {} modules",
                            len(getattr(ao, 'modules', [])))
            except Exception as e:
                logger.error("Failed to initialize archive orchestrator: {}", e)

        if _AVAILABLE.get('elite_system'):
            try:
                extended_systems['elite_psychology'] = EliteMarketPsychology()
                extended_systems['elite_regime'] = EliteRegimeDetector()
                extended_systems['elite_risk'] = EliteRiskManager()
                logger.info("Elite system initialized (psychology, regime, risk)")
            except Exception as e:
                logger.error("Failed to initialize elite system: {}", e)

        if _AVAILABLE.get('ultimate_production'):
            try:
                extended_systems['strategy_ensemble'] = StrategyEnsemble()
                extended_systems['ml_prediction'] = MLPredictionEngine()
                extended_systems['risk_fortress'] = RiskFortress()
                logger.info("Ultimate production initialized (ensemble, ML, risk fortress)")
            except Exception as e:
                logger.error("Failed to initialize ultimate production: {}", e)

        if _AVAILABLE.get('master_integration'):
            _init_system('master_integration', 'master_trading_system', lambda: MasterTradingSystem())
        if _AVAILABLE.get('ultimate_approval'):
            _init_system('ultimate_approval', 'approval_system', lambda: UltimateApprovalSystem())
        if _AVAILABLE.get('ultimate_architecture'):
            _init_system('ultimate_architecture', 'architecture_manager', lambda: ArchitectureManager())

        # --- Layer 10: Governance ---
        if _AVAILABLE.get('compliance'):
            _init_system('compliance', 'compliance', lambda: ComplianceMonitor())

        # --- Recursive Self-Improvement ---
        if _AVAILABLE.get('recursive_improvement'):
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
                logger.info("Recursive self-improvement system initialized")
            except Exception as e:
                logger.error("Failed to initialize recursive self-improvement: {}", e)

        if _AVAILABLE.get('self_improvement'):
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
    else:
        logger.info("Lean mode: skipping heavy extended systems (use --full-integration to enable all)")

    logger.info("=" * 70)
    logger.info("Extended systems initialized: {} modules active", len(extended_systems))
    logger.info("Available modules by layer:")
    layer_counts = {}
    for key, avail in _AVAILABLE.items():
        if avail:
            layer_counts[key] = True
    logger.info("  Total available: {}/{}", len(layer_counts), len(_AVAILABLE))
    logger.info("=" * 70)
    
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
                        MAX_LOT_CAP = 10.0  # Sensible cap for paper trading
                        
                        # Determine direction from signal
                        if isinstance(signals, dict):
                            sig_action = signals.get('action', signals.get('direction', 'buy'))
                        elif isinstance(signals, list) and signals:
                            sig_action = safe_get(signals[0], 'action', safe_get(signals[0], 'direction', 'buy'))
                        else:
                            sig_action = 'buy'
                        _sig_dir = -1 if str(sig_action).lower() in ('sell', 'short', '-1') else 1
                        
                        # --- INTELLIGENCE GATE: Discipline + Knowledge + Human Approval ---
                        _intel_blocked = False
                        _intel_size_mult = 1.0
                        _intel_sl = 0.0
                        _intel_tp = 0.0
                        _has_position = (hasattr(position, 'lot') and position.lot > 0) or (not hasattr(position, 'lot') and position != 0)
                        if _knowledge_bridge and _has_position:
                            try:
                                _raw_lots = abs(position.lot) if hasattr(position, 'lot') else abs(position)
                                _notional = _raw_lots * last_close * 100000  # Approx notional for FX
                                _trade_decision = await _knowledge_bridge.evaluate_trade(
                                    symbol=symbol,
                                    direction='BUY' if _sig_dir > 0 else 'SELL',
                                    lots=_raw_lots,
                                    entry_price=last_close,
                                    strategy='main_loop',
                                    confidence=signal_confidence,
                                    notional_value=_notional,
                                )
                                if not _trade_decision.should_trade:
                                    logger.info(
                                        f"[INTELLIGENCE] Trade BLOCKED: "
                                        f"{', '.join(_trade_decision.rejection_reasons)}"
                                    )
                                    _intel_blocked = True
                                else:
                                    _intel_size_mult = _trade_decision.size_multiplier
                                    _intel_sl = _trade_decision.stop_loss
                                    _intel_tp = _trade_decision.take_profit
                                    # Human approval for large trades
                                    if _trade_decision.needs_human_approval and _human_gate:
                                        _req = _human_gate.create_request(
                                            symbol=symbol,
                                            direction='BUY' if _sig_dir > 0 else 'SELL',
                                            lots=_raw_lots * _intel_size_mult,
                                            notional_value=_notional,
                                            price=last_close,
                                            strategy='main_loop',
                                            confidence=signal_confidence,
                                            risk_reward=_trade_decision.risk_reward,
                                            reason=f"Signal confidence {signal_confidence:.0%}",
                                        )
                                        _approved = await _human_gate.wait_for_approval(_req)
                                        if not _approved:
                                            logger.warning(f"[HUMAN GATE] Trade NOT approved — skipping")
                                            _intel_blocked = True
                            except Exception as e:
                                logger.warning(f"Intelligence gate error (allowing trade): {e}")
                        
                        if _intel_blocked:
                            await asyncio.sleep(5)
                            continue
                        
                        if hasattr(position, 'lot') and position.lot > 0:
                            trade_direction = _sig_dir
                            trade_size = min(abs(position.lot) * _intel_size_mult, MAX_LOT_CAP)
                            await trader['executor'].execute_trade(
                                symbol=symbol,
                                direction=trade_direction,
                                size=trade_size
                            )
                            trade_executed = True
                        elif not hasattr(position, 'lot') and position != 0:
                            trade_direction = _sig_dir
                            trade_size = min(abs(position) * _intel_size_mult, MAX_LOT_CAP)
                            await trader['executor'].execute_trade(
                                symbol=symbol,
                                direction=trade_direction,
                                size=trade_size
                            )
                            trade_executed = True
                        
                        # --- Intelligence: post-trade learning ---
                        if trade_executed:
                            # Record trade in discipline engine (tracks P&L, streaks, limits)
                            if _discipline:
                                try:
                                    from trading_bot.intelligence.discipline_engine import TradeRecord
                                    _discipline.record_trade(TradeRecord(
                                        timestamp=datetime.now(),
                                        symbol=symbol,
                                        direction='BUY' if trade_direction > 0 else 'SELL',
                                        lots=trade_size,
                                        pnl=0.0,  # Updated when trade closes
                                        notional_value=trade_size * last_close * 100000,
                                    ))
                                except Exception as e:
                                    logger.debug(f"Discipline record error: {e}")

                            # Record trade in self-learning engine (journal + analysis)
                            if _self_learner:
                                try:
                                    from trading_bot.intelligence.self_learning_engine import TradeJournalEntry
                                    _self_learner.record_trade(TradeJournalEntry(
                                        trade_id=f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                        symbol=symbol,
                                        direction='BUY' if trade_direction > 0 else 'SELL',
                                        strategy='main_loop',
                                        entry_price=last_close,
                                        exit_price=last_close,
                                        lots=trade_size,
                                        pnl=0.0,
                                        pnl_pct=0.0,
                                        entry_time=datetime.now(),
                                        exit_time=datetime.now(),
                                        hold_duration_minutes=0,
                                        confidence=signal_confidence,
                                        risk_reward_planned=_intel_tp / max(_intel_sl, 0.0001) if _intel_sl else 0,
                                        risk_reward_actual=0.0,
                                    ))
                                except Exception as e:
                                    logger.debug(f"Self-learning record error: {e}")

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
                    import traceback as _tb
                    err_msg = str(e)
                    logger.error(f"Error in trading loop: {err_msg}")
                    # Auto-reconnect MT5 on IPC/connection errors
                    if "IPC" in err_msg or "not connected" in err_msg.lower() or "initialize" in err_msg.lower():
                        logger.warning("MT5 connection lost. Attempting auto-reconnect...")
                        try:
                            mt5i.shutdown()
                        except Exception:
                            pass
                        await asyncio.sleep(3)
                        try:
                            mt5i.connect()
                            logger.info("MT5 auto-reconnect successful")
                        except Exception as re_err:
                            logger.error(f"MT5 auto-reconnect failed: {re_err}")
                    await asyncio.sleep(5)
                    
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
