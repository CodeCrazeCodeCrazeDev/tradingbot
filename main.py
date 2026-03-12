from __future__ import annotations
import sys
import os
import logging
import warnings
import inspect

# ============================================================================
# CRITICAL: Apply Unicode fix FIRST before any other imports
# ============================================================================
# Add trading_bot to path if needed
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Apply comprehensive Unicode fix for Windows
try:
    from trading_bot.unicode_fix import apply_unicode_fix, setup_utf8_logging
    apply_unicode_fix()
    setup_utf8_logging()
except ImportError:
    # Fallback if unicode_fix module not available
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

# Suppress Gym deprecation warning before any imports
os.environ['GYM_IGNORE_DEPRECATION_WARNING'] = '1'

# Suppress warnings for optional dependencies and deprecated packages
warnings.filterwarnings('ignore', message='.*Gym has been unmaintained.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='gym')
warnings.filterwarnings('ignore', category=UserWarning, module='gym')

# Temporarily suppress stderr to hide gym deprecation warning during imports
import io
_original_stderr = sys.stderr
sys.stderr = io.StringIO()

"""
Integrated Trading Bot - Main Entry Point

This main.py integrates individual modules from the trading_bot package structure.
It uses direct imports from individual files and modules for better maintainability
and explicit dependency management.

Key improvements:
1. Direct imports from individual files instead of directory-based loading
2. Explicit dependency management
3. Better error handling and fallbacks
4. Modular architecture with clear separation of concerns
5. Graceful degradation for missing modules

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
# CORE IMPORTS (from individual files)
# ============================================================================

# Core trading modules
try:
    from trading_bot.data.mt5_interface import MT5Interface
except Exception as e:
    logger.warning(f"MT5Interface import failed: {e}")
    MT5Interface = None

try:
    from trading_bot.strategy.strategy_engine import StrategyEngine
except Exception as e:
    logger.warning(f"StrategyEngine import failed: {e}")
    StrategyEngine = None

try:
    from trading_bot.strategy.ml_strategy import MLStrategyEngine
except Exception as e:
    logger.warning(f"MLStrategyEngine import failed: {e}")
    MLStrategyEngine = None

try:
    from trading_bot.execution.paper_executor import PaperExecutor
except Exception as e:
    logger.warning(f"PaperExecutor import failed: {e}")
    PaperExecutor = None

try:
    from trading_bot.execution.live_executor import LiveExecutor
except Exception as e:
    logger.warning(f"LiveExecutor import failed: {e}")
    LiveExecutor = None

try:
    from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
except Exception as e:
    logger.warning(f"Execution algorithms import failed: {e}")
    TWAPExecutor = None
    VWAPExecutor = None
    SmartOrderRouter = None

try:
    from trading_bot.risk.risk_manager import RiskManager
except Exception as e:
    logger.warning(f"RiskManager import failed: {e}")
    RiskManager = None

try:
    from trading_bot.analytics.performance_analytics import PerformanceAnalytics
except Exception as e:
    logger.warning(f"PerformanceAnalytics import failed: {e}")
    PerformanceAnalytics = None

try:
    from trading_bot.analytics.emotional_tracker import EmotionalStateTracker
except Exception as e:
    logger.warning(f"EmotionalStateTracker import failed: {e}")
    EmotionalStateTracker = None

# Core utilities
try:
    from trading_bot.config.config import get as config_get
except Exception as e:
    logger.warning(f"Config import failed: {e}")
    config_get = None

try:
    from trading_bot.reporting.logger import init_logger
except Exception as e:
    logger.warning(f"Logger import failed: {e}")
    def init_logger(level=None):
        logging.basicConfig(level=getattr(logging, level or 'INFO'))

try:
    from trading_bot.utils.profiler import profile_function
except Exception as e:
    logger.warning(f"Profiler import failed: {e}")
    def profile_function(level="INFO"):
        def decorator(func):
            return func
        return decorator

try:
    from trading_bot.utils.safe_access import safe_get
except Exception as e:
    logger.warning(f"Safe access import failed: {e}")
    def safe_get(data, key, default=None):
        try:
            return data.get(key, default) if hasattr(data, 'get') else default
        except:
            return default

# ============================================================================
# OPTIONAL MODULES (loaded dynamically with fallbacks)
# ============================================================================

# Track availability of optional modules
_AVAILABLE = {}

# ============================================================================
# MASTER INTEGRATION ENGINE  (world-class integration layer)
# ============================================================================
try:
    from trading_bot.integration import (
        MasterIntegrationEngine,
        EngineConfig,
        get_engine,
        get_module_registry,
        LegacyModuleAdapter,
    )
    _AVAILABLE['master_integration_engine'] = True
except Exception as _mie_err:
    logger.warning(f"MasterIntegrationEngine import failed: {_mie_err}")
    MasterIntegrationEngine = None
    EngineConfig = None
    get_engine = None
    get_module_registry = None
    LegacyModuleAdapter = None
    _AVAILABLE['master_integration_engine'] = False

# ============================================================================
# LAYER 1: CORE SYSTEMS INTEGRATION
# ============================================================================

# Elite AI System
try:
    from trading_bot.elite_ai_system import (
        EliteTradingOrchestrator,
        SlowInferenceEngine,
        MarketPsychologyEngine,
        EmergencyResponseSystem,
    )
    _AVAILABLE['elite_ai'] = True
except Exception as e:
    _AVAILABLE['elite_ai'] = False
    EliteTradingOrchestrator = None

# Market Intelligence System
try:
    from trading_bot.market_intelligence import (
        MarketDataMonitor,
        WyckoffAccumulationDetector,
        WyckoffDistributionAnalyzer,
        LiquidityPoolDetector,
        OrderBlockAnalysis,
        MarketEventDetector,
        PricePatternRecognition,
    )
    _AVAILABLE['market_intelligence'] = True
except Exception as e:
    _AVAILABLE['market_intelligence'] = False
    MarketDataMonitor = None

# 100% Complete System
try:
    from trading_bot.master_integration import MasterTradingSystem
    _AVAILABLE['complete_system'] = True
except Exception as e:
    _AVAILABLE['complete_system'] = False
    MasterTradingSystem = None

# Enhanced Risk Management
try:
    from trading_bot.risk.complete_risk_system import CompleteRiskSystem
    _AVAILABLE['enhanced_risk'] = True
except Exception as e:
    _AVAILABLE['enhanced_risk'] = False
    CompleteRiskSystem = None

# Smart Execution
try:
    from trading_bot.execution.complete_execution_system import CompleteExecutionSystem
    _AVAILABLE['smart_execution'] = True
except Exception as e:
    _AVAILABLE['smart_execution'] = False
    CompleteExecutionSystem = None

# Performance Analytics
try:
    from trading_bot.performance.complete_performance_system import CompletePerformanceSystem
    _AVAILABLE['performance_analytics'] = True
except Exception as e:
    _AVAILABLE['performance_analytics'] = False
    CompletePerformanceSystem = None

# Market Student (Learning System)
try:
    from trading_bot.market_student import MarketStudentOrchestrator
    _AVAILABLE['market_student'] = True
except Exception as e:
    _AVAILABLE['market_student'] = False
    MarketStudentOrchestrator = None

# Eternal Evolution (Auto-tuning)
try:
    from trading_bot.eternal_evolution import EternalEvolutionOrchestrator
    _AVAILABLE['eternal_evolution'] = True
except Exception as e:
    _AVAILABLE['eternal_evolution'] = False
    EternalEvolutionOrchestrator = None

# Self-Diagnostic System
try:
    from trading_bot.self_diagnostic import SelfManager
    _AVAILABLE['self_diagnostic'] = True
except Exception as e:
    _AVAILABLE['self_diagnostic'] = False
    SelfManager = None

# Hedge Fund Safety
try:
    from trading_bot.hedge_fund_safety import HedgeFundSafetyOrchestrator
    _AVAILABLE['hedge_fund_safety'] = True
except Exception as e:
    _AVAILABLE['hedge_fund_safety'] = False
    HedgeFundSafetyOrchestrator = None

# Alpha Research
try:
    from trading_bot.alpha_research import AlphaResearchOrchestrator
    _AVAILABLE['alpha_research'] = True
except Exception as e:
    _AVAILABLE['alpha_research'] = False
    AlphaResearchOrchestrator = None

# Intelligent Delegation
try:
    from trading_bot.intelligent_delegation import DelegationOrchestrator
    _AVAILABLE['intelligent_delegation'] = True
except Exception as e:
    _AVAILABLE['intelligent_delegation'] = False
    DelegationOrchestrator = None

# Trading Engine
try:
    from trading_bot.trading_engine import TradingEngine
    _AVAILABLE['trading_engine'] = True
except Exception as e:
    _AVAILABLE['trading_engine'] = False
    TradingEngine = None

# Master Orchestrator (Main Coordinator)
try:
    from trading_bot.master_orchestrator import MasterOrchestrator as MainMasterOrchestrator
    _AVAILABLE['main_orchestrator'] = True
except Exception as e:
    _AVAILABLE['main_orchestrator'] = False
    MainMasterOrchestrator = None

# Unified AI Brain
try:
    from trading_bot.unified_ai_brain import UnifiedAIBrain, BrainConfig
    _AVAILABLE['unified_brain'] = True
except Exception as e:
    _AVAILABLE['unified_brain'] = False
    UnifiedAIBrain = None
    BrainConfig = None

# Reality Gates (Pre-execution checks)
try:
    from trading_bot.reality_gates import RealityGateOrchestrator
    _AVAILABLE['reality_gates'] = True
except Exception as e:
    _AVAILABLE['reality_gates'] = False
    RealityGateOrchestrator = None

# Safety Systems
try:
    from trading_bot.safety import SafetyOrchestrator
    _AVAILABLE['safety'] = True
except Exception as e:
    _AVAILABLE['safety'] = False
    SafetyOrchestrator = None

# Stealth Safety
try:
    from trading_bot.stealth_safety import StealthSafetyManager
    _AVAILABLE['stealth_safety'] = True
except Exception as e:
    _AVAILABLE['stealth_safety'] = False
    StealthSafetyManager = None

# Compliance
try:
    from trading_bot.compliance import ComplianceManager
    _AVAILABLE['compliance'] = True
except Exception as e:
    _AVAILABLE['compliance'] = False
    ComplianceManager = None

# Position Management
try:
    from trading_bot.position import PositionManager
    _AVAILABLE['position_manager'] = True
except Exception as e:
    _AVAILABLE['position_manager'] = False
    PositionManager = None

# AI Core
try:
    from trading_bot.ai_core import AICoreOrchestrator
    _AVAILABLE['ai_core'] = True
except Exception as e:
    _AVAILABLE['ai_core'] = False
    AICoreOrchestrator = None

# Brain System
try:
    from trading_bot.brain import BrainOrchestrator
    _AVAILABLE['brain'] = True
except Exception as e:
    _AVAILABLE['brain'] = False
    BrainOrchestrator = None

# Alpha Engine
try:
    from trading_bot.alpha_engine import AlphaEngine
    _AVAILABLE['alpha_engine'] = True
except Exception as e:
    _AVAILABLE['alpha_engine'] = False
    AlphaEngine = None

# Decision Layer
try:
    from trading_bot.decision_layer import DecisionLayerOrchestrator
    _AVAILABLE['decision_layer'] = True
except Exception as e:
    _AVAILABLE['decision_layer'] = False
    DecisionLayerOrchestrator = None

# Cognitive Architecture
try:
    from trading_bot.cognitive_architecture import CognitiveOrchestrator
    _AVAILABLE['cognitive'] = True
except Exception as e:
    _AVAILABLE['cognitive'] = False
    CognitiveOrchestrator = None

# Profit Maximizer
try:
    from trading_bot.profit_maximizer import ProfitMaximizer
    _AVAILABLE['profit_maximizer'] = True
except Exception as e:
    _AVAILABLE['profit_maximizer'] = False
    ProfitMaximizer = None

# AAMIS V3 System
try:
    from trading_bot.aamis_v3 import AAMISOrchestrator
    _AVAILABLE['aamis_v3'] = True
except Exception as e:
    _AVAILABLE['aamis_v3'] = False
    AAMISOrchestrator = None

# AlphaAlgo Core
try:
    from trading_bot.alphaalgo_core import AlphaAlgoCore
    _AVAILABLE['alphaalgo_core'] = True
except Exception as e:
    _AVAILABLE['alphaalgo_core'] = False
    AlphaAlgoCore = None

# Sentient Core
try:
    from trading_bot.sentient_core import SentientOrchestrator
    _AVAILABLE['sentient_core'] = True
except Exception as e:
    _AVAILABLE['sentient_core'] = False
    SentientOrchestrator = None

# Ingestion Pipeline
try:
    from trading_bot.ingestion import IngestionOrchestrator
    _AVAILABLE['ingestion'] = True
except Exception as e:
    _AVAILABLE['ingestion'] = False
    IngestionOrchestrator = None

# Streaming
try:
    from trading_bot.streaming import StreamingManager
    _AVAILABLE['streaming'] = True
except Exception as e:
    _AVAILABLE['streaming'] = False
    StreamingManager = None

# Data Feeds
try:
    from trading_bot.data_feeds import DataFeedManager
    _AVAILABLE['data_feeds'] = True
except Exception as e:
    _AVAILABLE['data_feeds'] = False
    DataFeedManager = None

# Database
try:
    from trading_bot.database import DatabaseManager
    _AVAILABLE['database'] = True
except Exception as e:
    _AVAILABLE['database'] = False
    DatabaseManager = None

# Monitoring
try:
    from trading_bot.monitoring import MonitoringOrchestrator
    _AVAILABLE['monitoring'] = True
except Exception as e:
    _AVAILABLE['monitoring'] = False
    MonitoringOrchestrator = None

# System Health
try:
    from trading_bot.system_health import SystemHealthManager
    _AVAILABLE['system_health'] = True
except Exception as e:
    _AVAILABLE['system_health'] = False
    SystemHealthManager = None

# System Supervisor
try:
    from trading_bot.system_supervisor import SystemSupervisor
    _AVAILABLE['system_supervisor'] = True
except Exception as e:
    _AVAILABLE['system_supervisor'] = False
    SystemSupervisor = None

# Event Monitoring
try:
    from trading_bot.event_monitoring import EventMonitor
    _AVAILABLE['event_monitoring'] = True
except Exception as e:
    _AVAILABLE['event_monitoring'] = False
    EventMonitor = None

# Observability
try:
    from trading_bot.observability import ObservabilityManager
    _AVAILABLE['observability'] = True
except Exception as e:
    _AVAILABLE['observability'] = False
    ObservabilityManager = None

# Telemetry
try:
    from trading_bot.telemetry import TelemetryManager
    _AVAILABLE['telemetry'] = True
except Exception as e:
    _AVAILABLE['telemetry'] = False
    TelemetryManager = None

# Notifications
try:
    from trading_bot.notifications import NotificationManager
    _AVAILABLE['notifications'] = True
except Exception as e:
    _AVAILABLE['notifications'] = False
    NotificationManager = None

# Alerts
try:
    from trading_bot.alerts import AlertManager
    _AVAILABLE['alerts'] = True
except Exception as e:
    _AVAILABLE['alerts'] = False
    AlertManager = None

# Audit
try:
    from trading_bot.audit import AuditManager
    _AVAILABLE['audit'] = True
except Exception as e:
    _AVAILABLE['audit'] = False
    AuditManager = None

# Governance
try:
    from trading_bot.governance import GovernanceManager
    _AVAILABLE['governance'] = True
except Exception as e:
    _AVAILABLE['governance'] = False
    GovernanceManager = None

# World Model
try:
    from trading_bot.world_model import WorldModel
    _AVAILABLE['world_model'] = True
except Exception as e:
    _AVAILABLE['world_model'] = False
    WorldModel = None

# Quantum Computing
try:
    from trading_bot.quantum import QuantumOptimizer
    _AVAILABLE['quantum'] = True
except Exception as e:
    _AVAILABLE['quantum'] = False
    QuantumOptimizer = None

# Blockchain
try:
    from trading_bot.blockchain import BlockchainValidator
    _AVAILABLE['blockchain'] = True
except Exception as e:
    _AVAILABLE['blockchain'] = False
    BlockchainValidator = None

# Arbitrage
try:
    from trading_bot.arbitrage import ArbitrageScanner
    _AVAILABLE['arbitrage'] = True
except Exception as e:
    _AVAILABLE['arbitrage'] = False
    ArbitrageScanner = None

# Portfolio Management
try:
    from trading_bot.portfolio import PortfolioManager
    _AVAILABLE['portfolio'] = True
except Exception as e:
    _AVAILABLE['portfolio'] = False
    PortfolioManager = None

# Multimodal AI
try:
    from trading_bot.multimodal import MultimodalAnalyzer
    _AVAILABLE['multimodal'] = True
except Exception as e:
    _AVAILABLE['multimodal'] = False
    MultimodalAnalyzer = None

# Autonomous Systems
try:
    from trading_bot.autonomous import AutonomousOrchestrator
    _AVAILABLE['autonomous'] = True
except Exception as e:
    _AVAILABLE['autonomous'] = False
    AutonomousOrchestrator = None

# Self Improvement
try:
    from trading_bot.self_improvement import SelfImprovementEngine
    _AVAILABLE['self_improvement'] = True
except Exception as e:
    _AVAILABLE['self_improvement'] = False
    SelfImprovementEngine = None

# Self Learning
try:
    from trading_bot.self_learning import SelfLearningEngine
    _AVAILABLE['self_learning'] = True
except Exception as e:
    _AVAILABLE['self_learning'] = False
    SelfLearningEngine = None

# Self Healing AI
try:
    from trading_bot.self_healing_ai import SelfHealingOrchestrator
    _AVAILABLE['self_healing'] = True
except Exception as e:
    _AVAILABLE['self_healing'] = False
    SelfHealingOrchestrator = None

# Recursive Improvement
try:
    from trading_bot.recursive_improvement import RecursiveImprovementEngine
    _AVAILABLE['recursive_improvement'] = True
except Exception as e:
    _AVAILABLE['recursive_improvement'] = False
    RecursiveImprovementEngine = None

# Complete Pipeline Orchestrator
try:
    from trading_bot.complete_pipeline_orchestrator import CompletePipelineOrchestrator
    _AVAILABLE['complete_pipeline'] = True
except Exception as e:
    _AVAILABLE['complete_pipeline'] = False
    CompletePipelineOrchestrator = None

# Complete System Integrator
try:
    from trading_bot.complete_system_integrator import CompleteSystemIntegrator
    _AVAILABLE['complete_integrator'] = True
except Exception as e:
    _AVAILABLE['complete_integrator'] = False
    CompleteSystemIntegrator = None

# Ultimate Integration
try:
    from trading_bot.ultimate_integration import UltimateIntegration
    _AVAILABLE['ultimate_integration'] = True
except Exception as e:
    _AVAILABLE['ultimate_integration'] = False
    UltimateIntegration = None

# Unified Master Integrator
try:
    from trading_bot.unified_master_integrator import UnifiedMasterIntegrator
    _AVAILABLE['unified_integrator'] = True
except Exception as e:
    _AVAILABLE['unified_integrator'] = False
    UnifiedMasterIntegrator = None

# Mega Integration
try:
    from trading_bot.mega_integration import MegaIntegration
    _AVAILABLE['mega_integration'] = True
except Exception as e:
    _AVAILABLE['mega_integration'] = False
    MegaIntegration = None

# Elite Master System
try:
    from trading_bot.elite_master_system import EliteMasterSystem
    _AVAILABLE['elite_master'] = True
except Exception as e:
    _AVAILABLE['elite_master'] = False
    EliteMasterSystem = None

# Master System
try:
    from trading_bot.master_system import MasterSystem
    _AVAILABLE['master_system'] = True
except Exception as e:
    _AVAILABLE['master_system'] = False
    MasterSystem = None

# Realtime Trading Core
try:
    from trading_bot.realtime_trading_core import RealtimeTradingCore
    _AVAILABLE['realtime_core'] = True
except Exception as e:
    _AVAILABLE['realtime_core'] = False
    RealtimeTradingCore = None

# Optimized Integration
try:
    from trading_bot.optimized_integration import OptimizedIntegration
    _AVAILABLE['optimized_integration'] = True
except Exception as e:
    _AVAILABLE['optimized_integration'] = False
    OptimizedIntegration = None

# Elite Integration
try:
    from trading_bot.elite_integration import EliteIntegration
    _AVAILABLE['elite_integration'] = True
except Exception as e:
    _AVAILABLE['elite_integration'] = False
    EliteIntegration = None

# Archive Orchestrator
try:
    from trading_bot.archive_orchestrator import ArchiveOrchestrator
    _AVAILABLE['archive_orchestrator'] = True
except Exception as e:
    _AVAILABLE['archive_orchestrator'] = False
    ArchiveOrchestrator = None

# AlphaAlgo 5-Star
try:
    from trading_bot.alphaalgo_5star import AlphaAlgo5Star
    _AVAILABLE['alphaalgo_5star'] = True
except Exception as e:
    _AVAILABLE['alphaalgo_5star'] = False
    AlphaAlgo5Star = None

# Market Teacher
try:
    from trading_bot.market_teacher import MarketTeacherOrchestrator
    _AVAILABLE['market_teacher'] = True
except Exception as e:
    _AVAILABLE['market_teacher'] = False
    MarketTeacherOrchestrator = None

# Autonomous Learner
try:
    from trading_bot.autonomous_learner import LearningOrchestrator
    _AVAILABLE['autonomous_learner'] = True
except Exception as e:
    _AVAILABLE['autonomous_learner'] = False
    LearningOrchestrator = None

# Improvement Agent
try:
    from trading_bot.improvement_agent import AgentOrchestrator
    _AVAILABLE['improvement_agent'] = True
except Exception as e:
    _AVAILABLE['improvement_agent'] = False
    AgentOrchestrator = None

# Self Mastery
try:
    from trading_bot.self_mastery import MasteryOrchestrator
    _AVAILABLE['self_mastery'] = True
except Exception as e:
    _AVAILABLE['self_mastery'] = False
    MasteryOrchestrator = None

# Superintelligence
try:
    from trading_bot.superintelligence import SuperintelligenceOrchestrator
    _AVAILABLE['superintelligence'] = True
except Exception as e:
    _AVAILABLE['superintelligence'] = False
    SuperintelligenceOrchestrator = None

# Advanced Analysis
try:
    from trading_bot.advanced_analysis import AdvancedAnalysisOrchestrator
    _AVAILABLE['advanced_analysis'] = True
except Exception as e:
    _AVAILABLE['advanced_analysis'] = False
    AdvancedAnalysisOrchestrator = None

# Adversarial Curriculum
try:
    from trading_bot.adversarial_curriculum import CurriculumOrchestrator
    _AVAILABLE['adversarial_curriculum'] = True
except Exception as e:
    _AVAILABLE['adversarial_curriculum'] = False
    CurriculumOrchestrator = None

# Offline RL Continuous Learning
try:
    from trading_bot.ml.offline_rl import ContinuousLearningOrchestrator
    _AVAILABLE['offline_rl_continuous'] = True
except Exception as e:
    _AVAILABLE['offline_rl_continuous'] = False
    ContinuousLearningOrchestrator = None

# Research Ingestion
try:
    from trading_bot.research_ingestion import ResearchPipelineOrchestrator
    _AVAILABLE['research_ingestion'] = True
except Exception as e:
    _AVAILABLE['research_ingestion'] = False
    ResearchPipelineOrchestrator = None

 
# Realtime Orchestrator
try:
    from trading_bot.realtime import RealtimeOrchestrator
    _AVAILABLE['realtime_orchestrator'] = True
except Exception as e:
    _AVAILABLE['realtime_orchestrator'] = False
    RealtimeOrchestrator = None

# Ultimate System
try:
    from trading_bot.ultimate_system import UltimateOrchestrator
    _AVAILABLE['ultimate_system'] = True
except Exception as e:
    _AVAILABLE['ultimate_system'] = False
    UltimateOrchestrator = None

# Unified System
try:
    from trading_bot.unified_system import UnifiedSystemOrchestrator
    _AVAILABLE['unified_system'] = True
except Exception as e:
    _AVAILABLE['unified_system'] = False
    UnifiedSystemOrchestrator = None

# DeepChart Market Intelligence
try:
    from trading_bot.deepchart import MarketIntelligenceOrchestrator
    _AVAILABLE['deepchart'] = True
except Exception as e:
    _AVAILABLE['deepchart'] = False
    MarketIntelligenceOrchestrator = None

# MSOS (Market Survival Operating System)
try:
    from trading_bot.msos import MSOSOrchestrator
    _AVAILABLE['msos'] = True
except Exception as e:
    _AVAILABLE['msos'] = False
    MSOSOrchestrator = None

# Systems AI
try:
    from trading_bot.systems_ai import SystemsAIOrchestrator
    _AVAILABLE['systems_ai'] = True
except Exception as e:
    _AVAILABLE['systems_ai'] = False
    SystemsAIOrchestrator = None

# Event Pipeline
try:
    from trading_bot.event_pipeline import EventPipeline
    _AVAILABLE['event_pipeline'] = True
except Exception as e:
    _AVAILABLE['event_pipeline'] = False
    EventPipeline = None

# Hedge Fund Operations
try:
    from trading_bot.hedge_fund import HedgeFundOrchestrator
    _AVAILABLE['hedge_fund'] = True
except Exception as e:
    _AVAILABLE['hedge_fund'] = False
    HedgeFundOrchestrator = None

# AlphaAlgo V2
try:
    from trading_bot.alphaalgo_v2 import AlphaAlgoV2Orchestrator
    _AVAILABLE['alphaalgo_v2'] = True
except Exception as e:
    _AVAILABLE['alphaalgo_v2'] = False
    AlphaAlgoV2Orchestrator = None

# AlphaAlgo Institutional
try:
    from trading_bot.alphaalgo_institutional import InstitutionalOrchestrator
    _AVAILABLE['alphaalgo_institutional'] = True
except Exception as e:
    _AVAILABLE['alphaalgo_institutional'] = False
    InstitutionalOrchestrator = None

# Realtime Trading Core
try:
    from trading_bot.realtime import RealtimeOrchestrator as RealtimeCoreOrchestrator
    _AVAILABLE['realtime_core_orchestrator'] = True
except Exception as e:
    _AVAILABLE['realtime_core_orchestrator'] = False
    RealtimeCoreOrchestrator = None

    # AAMIS V3
try:
    from trading_bot.aamis_v3 import AAMISOrchestrator as AAMIS_V3_Orchestrator
    _AVAILABLE['aamis_v3_full'] = True
except Exception as e:
    _AVAILABLE['aamis_v3_full'] = False
    AAMIS_V3_Orchestrator = None

# Adversarial Decision
try:
    from trading_bot.adversarial_decision import AdversarialDecisionOrchestrator
    _AVAILABLE['adversarial_decision'] = True
except Exception as e:
    _AVAILABLE['adversarial_decision'] = False
    AdversarialDecisionOrchestrator = None

# Agents
try:
    from trading_bot.agents import AgentManager
    _AVAILABLE['agents'] = True
except Exception as e:
    _AVAILABLE['agents'] = False
    AgentManager = None

# Agents2
try:
    from trading_bot.agents2 import Agent2Manager
    _AVAILABLE['agents2'] = True
except Exception as e:
    _AVAILABLE['agents2'] = False
    Agent2Manager = None

# Autonomous Pipeline
try:
    from trading_bot.autonomous_pipeline import AutonomousPipelineOrchestrator
    _AVAILABLE['autonomous_pipeline'] = True
except Exception as e:
    _AVAILABLE['autonomous_pipeline'] = False
    AutonomousPipelineOrchestrator = None

# Evolution Layer
try:
    from trading_bot.evolution_layer import EvolutionLayerOrchestrator
    _AVAILABLE['evolution_layer'] = True
except Exception as e:
    _AVAILABLE['evolution_layer'] = False
    EvolutionLayerOrchestrator = None

# HFT (High-Frequency Trading)
try:
    from trading_bot.hft import HFTOrchestrator
    _AVAILABLE['hft'] = True
except Exception as e:
    _AVAILABLE['hft'] = False
    HFTOrchestrator = None

# Institutional Entry
try:
    from trading_bot.institutional_entry import InstitutionalEntryOrchestrator
    _AVAILABLE['institutional_entry'] = True
except Exception as e:
    _AVAILABLE['institutional_entry'] = False
    InstitutionalEntryOrchestrator = None

# Innovations
try:
    from trading_bot.innovations import InnovationOrchestrator
    _AVAILABLE['innovations'] = True
except Exception as e:
    _AVAILABLE['innovations'] = False
    InnovationOrchestrator = None

# Adaptive Systems
try:
    from trading_bot.adaptive_systems import AdaptiveSystemsOrchestrator
    _AVAILABLE['adaptive_systems_full'] = True
except Exception as e:
    _AVAILABLE['adaptive_systems_full'] = False
    AdaptiveSystemsOrchestrator = None

# Advanced Analysis
try:
    from trading_bot.advanced_analysis import AdvancedAnalysisOrchestrator as AdvancedAnalysisFull
    _AVAILABLE['advanced_analysis_full'] = True
except Exception as e:
    _AVAILABLE['advanced_analysis_full'] = False
    AdvancedAnalysisFull = None

# Advanced Features
try:
    from trading_bot.advanced_features import AdvancedFeaturesOrchestrator
    _AVAILABLE['advanced_features'] = True
except Exception as e:
    _AVAILABLE['advanced_features'] = False
    AdvancedFeaturesOrchestrator = None

# Advanced ML
try:
    from trading_bot.advanced_ml import AdvancedMLOrchestrator
    _AVAILABLE['advanced_ml'] = True
except Exception as e:
    _AVAILABLE['advanced_ml'] = False
    AdvancedMLOrchestrator = None

# Advanced Systems 2
try:
    from trading_bot.advanced_systems2 import AdvancedSystems2Orchestrator
    _AVAILABLE['advanced_systems2'] = True
except Exception as e:
    _AVAILABLE['advanced_systems2'] = False
    AdvancedSystems2Orchestrator = None

# AI Engineer
try:
    from trading_bot.ai_engineer import AIEngineerOrchestrator
    _AVAILABLE['ai_engineer'] = True
except Exception as e:
    _AVAILABLE['ai_engineer'] = False
    AIEngineerOrchestrator = None

# Analysis (full)
try:
    from trading_bot.analysis import AnalysisOrchestrator as AnalysisFull
    _AVAILABLE['analysis_full'] = True
except Exception as e:
    _AVAILABLE['analysis_full'] = False
    AnalysisFull = None

# Analysis Unified
try:
    from trading_bot.analysis_unified import UnifiedAnalysisOrchestrator
    _AVAILABLE['analysis_unified'] = True
except Exception as e:
    _AVAILABLE['analysis_unified'] = False
    UnifiedAnalysisOrchestrator = None

# API
try:
    from trading_bot.api import APIOrchestrator
    _AVAILABLE['api'] = True
except Exception as e:
    _AVAILABLE['api'] = False
    APIOrchestrator = None

# Approval
try:
    from trading_bot.approval import ApprovalManager
    _AVAILABLE['approval'] = True
except Exception as e:
    _AVAILABLE['approval'] = False
    ApprovalManager = None

# Auto Optimizer
try:
    from trading_bot.auto_optimizer import AutoOptimizerOrchestrator
    _AVAILABLE['auto_optimizer'] = True
except Exception as e:
    _AVAILABLE['auto_optimizer'] = False
    AutoOptimizerOrchestrator = None

# Automation
try:
    from trading_bot.automation import AutomationOrchestrator
    _AVAILABLE['automation'] = True
except Exception as e:
    _AVAILABLE['automation'] = False
    AutomationOrchestrator = None

# Bridges
try:
    from trading_bot.bridges import BridgeOrchestrator
    _AVAILABLE['bridges'] = True
except Exception as e:
    _AVAILABLE['bridges'] = False
    BridgeOrchestrator = None

# Broker
try:
    from trading_bot.broker import BrokerOrchestrator
    _AVAILABLE['broker'] = True
except Exception as e:
    _AVAILABLE['broker'] = False
    BrokerOrchestrator = None

# Calendar
try:
    from trading_bot.calendar import CalendarManager
    _AVAILABLE['calendar'] = True
except Exception as e:
    _AVAILABLE['calendar'] = False
    CalendarManager = None

# Cloud Deployer
try:
    from trading_bot.cloud_deployer import CloudDeployerOrchestrator
    _AVAILABLE['cloud_deployer'] = True
except Exception as e:
    _AVAILABLE['cloud_deployer'] = False
    CloudDeployerOrchestrator = None

# Connectivity Unified
try:
    from trading_bot.connectivity_unified import UnifiedConnectivityOrchestrator
    _AVAILABLE['connectivity_unified'] = True
except Exception as e:
    _AVAILABLE['connectivity_unified'] = False
    UnifiedConnectivityOrchestrator = None

# Connectors
try:
    from trading_bot.connectors import ConnectorOrchestrator
    _AVAILABLE['connectors'] = True
except Exception as e:
    _AVAILABLE['connectors'] = False
    ConnectorOrchestrator = None

# Core API
try:
    from trading_bot.core_api import CoreAPIOrchestrator
    _AVAILABLE['core_api'] = True
except Exception as e:
    _AVAILABLE['core_api'] = False
    CoreAPIOrchestrator = None

# Critical Fixes
try:
    from trading_bot.critical_fixes import CriticalFixesManager
    _AVAILABLE['critical_fixes'] = True
except Exception as e:
    _AVAILABLE['critical_fixes'] = False
    CriticalFixesManager = None

# Crypto
try:
    from trading_bot.crypto import CryptoOrchestrator
    _AVAILABLE['crypto'] = True
except Exception as e:
    _AVAILABLE['crypto'] = False
    CryptoOrchestrator = None

# cTrader
try:
    from trading_bot.ctrader import CTraderOrchestrator
    _AVAILABLE['ctrader'] = True
except Exception as e:
    _AVAILABLE['ctrader'] = False
    CTraderOrchestrator = None

# Deployment
try:
    from trading_bot.deployment import DeploymentOrchestrator
    _AVAILABLE['deployment'] = True
except Exception as e:
    _AVAILABLE['deployment'] = False
    DeploymentOrchestrator = None

# Derivatives
try:
    from trading_bot.derivatives import DerivativesOrchestrator
    _AVAILABLE['derivatives'] = True
except Exception as e:
    _AVAILABLE['derivatives'] = False
    DerivativesOrchestrator = None

# DevOps
try:
    from trading_bot.devops import DevOpsOrchestrator
    _AVAILABLE['devops'] = True
except Exception as e:
    _AVAILABLE['devops'] = False
    DevOpsOrchestrator = None

# Diagnostics
try:
    from trading_bot.diagnostics import DiagnosticsOrchestrator
    _AVAILABLE['diagnostics'] = True
except Exception as e:
    _AVAILABLE['diagnostics'] = False
    DiagnosticsOrchestrator = None

# Distributed
try:
    from trading_bot.distributed import DistributedOrchestrator
    _AVAILABLE['distributed'] = True
except Exception as e:
    _AVAILABLE['distributed'] = False
    DistributedOrchestrator = None

# Documentation
try:
    from trading_bot.documentation import DocumentationGenerator
    _AVAILABLE['documentation'] = True
except Exception as e:
    _AVAILABLE['documentation'] = False
    DocumentationGenerator = None

# Error Handling
try:
    from trading_bot.error_handling import ErrorHandlingOrchestrator
    _AVAILABLE['error_handling'] = True
except Exception as e:
    _AVAILABLE['error_handling'] = False
    ErrorHandlingOrchestrator = None

# Exit Strategies (full)
try:
    from trading_bot.exit_strategies import ExitStrategyOrchestrator
    _AVAILABLE['exit_strategies_full'] = True
except Exception as e:
    _AVAILABLE['exit_strategies_full'] = False
    ExitStrategyOrchestrator = None

# Exits
try:
    from trading_bot.exits import ExitsOrchestrator
    _AVAILABLE['exits'] = True
except Exception as e:
    _AVAILABLE['exits'] = False
    ExitsOrchestrator = None

# Explainability
try:
    from trading_bot.explainability import ExplainabilityOrchestrator
    _AVAILABLE['explainability'] = True
except Exception as e:
    _AVAILABLE['explainability'] = False
    ExplainabilityOrchestrator = None

# Features
try:
    from trading_bot.features import FeatureOrchestrator
    _AVAILABLE['features'] = True
except Exception as e:
    _AVAILABLE['features'] = False
    FeatureOrchestrator = None

# Filters
try:
    from trading_bot.filters import FilterOrchestrator
    _AVAILABLE['filters'] = True
except Exception as e:
    _AVAILABLE['filters'] = False
    FilterOrchestrator = None

# Global Expansion
try:
    from trading_bot.global_expansion import GlobalExpansionOrchestrator
    _AVAILABLE['global_expansion'] = True
except Exception as e:
    _AVAILABLE['global_expansion'] = False
    GlobalExpansionOrchestrator = None

# Hedging
try:
    from trading_bot.hedging import HedgingOrchestrator
    _AVAILABLE['hedging'] = True
except Exception as e:
    _AVAILABLE['hedging'] = False
    HedgingOrchestrator = None

# Human Layer
try:
    from trading_bot.human_layer import HumanLayerOrchestrator
    _AVAILABLE['human_layer'] = True
except Exception as e:
    _AVAILABLE['human_layer'] = False
    HumanLayerOrchestrator = None

# Improvements
try:
    from trading_bot.improvements import ImprovementsOrchestrator
    _AVAILABLE['improvements'] = True
except Exception as e:
    _AVAILABLE['improvements'] = False
    ImprovementsOrchestrator = None

# Indicators
try:
    from trading_bot.indicators import IndicatorOrchestrator
    _AVAILABLE['indicators'] = True
except Exception as e:
    _AVAILABLE['indicators'] = False
    IndicatorOrchestrator = None

# Intel
try:
    from trading_bot.intel import IntelOrchestrator
    _AVAILABLE['intel'] = True
except Exception as e:
    _AVAILABLE['intel'] = False
    IntelOrchestrator = None

# Intelligence (full)
try:
    from trading_bot.intelligence import IntelligenceOrchestrator as IntelligenceFull
    _AVAILABLE['intelligence_full'] = True
except Exception as e:
    _AVAILABLE['intelligence_full'] = False
    IntelligenceFull = None

# Internet Access
try:
    from trading_bot.internet_access import InternetAccessOrchestrator
    _AVAILABLE['internet_access'] = True
except Exception as e:
    _AVAILABLE['internet_access'] = False
    InternetAccessOrchestrator = None

# Learning
try:
    from trading_bot.learning import LearningOrchestrator as LearningFull
    _AVAILABLE['learning_full'] = True
except Exception as e:
    _AVAILABLE['learning_full'] = False
    LearningFull = None

# Log System
try:
    from trading_bot.log_system import LogSystemOrchestrator
    _AVAILABLE['log_system'] = True
except Exception as e:
    _AVAILABLE['log_system'] = False
    LogSystemOrchestrator = None

# Macro
try:
    from trading_bot.macro import MacroOrchestrator
    _AVAILABLE['macro'] = True
except Exception as e:
    _AVAILABLE['macro'] = False
    MacroOrchestrator = None

# Market Making
try:
    from trading_bot.market_making import MarketMakingOrchestrator
    _AVAILABLE['market_making'] = True
except Exception as e:
    _AVAILABLE['market_making'] = False
    MarketMakingOrchestrator = None

# Meta Learning
try:
    from trading_bot.meta_learning import MetaLearningOrchestrator
    _AVAILABLE['meta_learning'] = True
except Exception as e:
    _AVAILABLE['meta_learning'] = False
    MetaLearningOrchestrator = None

# Mobile
try:
    from trading_bot.mobile import MobileOrchestrator
    _AVAILABLE['mobile'] = True
except Exception as e:
    _AVAILABLE['mobile'] = False
    MobileOrchestrator = None

# Mobile App
try:
    from trading_bot.mobile_app import MobileAppOrchestrator
    _AVAILABLE['mobile_app'] = True
except Exception as e:
    _AVAILABLE['mobile_app'] = False
    MobileAppOrchestrator = None

# Ops
try:
    from trading_bot.ops import OpsOrchestrator
    _AVAILABLE['ops'] = True
except Exception as e:
    _AVAILABLE['ops'] = False
    OpsOrchestrator = None

# Optimization (full)
try:
    from trading_bot.optimization import OptimizationOrchestrator as OptimizationFull
    _AVAILABLE['optimization_full'] = True
except Exception as e:
    _AVAILABLE['optimization_full'] = False
    OptimizationFull = None

# Persistence
try:
    from trading_bot.persistence import PersistenceOrchestrator
    _AVAILABLE['persistence'] = True
except Exception as e:
    _AVAILABLE['persistence'] = False
    PersistenceOrchestrator = None

# Production
try:
    from trading_bot.production import ProductionOrchestrator
    _AVAILABLE['production'] = True
except Exception as e:
    _AVAILABLE['production'] = False
    ProductionOrchestrator = None

# Profiling
try:
    from trading_bot.profiling import ProfilingOrchestrator
    _AVAILABLE['profiling'] = True
except Exception as e:
    _AVAILABLE['profiling'] = False
    ProfilingOrchestrator = None

# Psychology
try:
    from trading_bot.psychology import PsychologyOrchestrator
    _AVAILABLE['psychology'] = True
except Exception as e:
    _AVAILABLE['psychology'] = False
    PsychologyOrchestrator = None

# Quality
try:
    from trading_bot.quality import QualityOrchestrator
    _AVAILABLE['quality'] = True
except Exception as e:
    _AVAILABLE['quality'] = False
    QualityOrchestrator = None

# Qwen CodeMender
try:
    from trading_bot.qwen_codemender import QwenCodeMenderOrchestrator
    _AVAILABLE['qwen_codemender'] = True
except Exception as e:
    _AVAILABLE['qwen_codemender'] = False
    QwenCodeMenderOrchestrator = None

# Reasoning
try:
    from trading_bot.reasoning import ReasoningOrchestrator
    _AVAILABLE['reasoning'] = True
except Exception as e:
    _AVAILABLE['reasoning'] = False
    ReasoningOrchestrator = None

# Research
try:
    from trading_bot.research import ResearchOrchestrator
    _AVAILABLE['research'] = True
except Exception as e:
    _AVAILABLE['research'] = False
    ResearchOrchestrator = None

# Risk Management (separate from risk/)
try:
    from trading_bot.risk_management import RiskManagementOrchestrator
    _AVAILABLE['risk_management'] = True
except Exception as e:
    _AVAILABLE['risk_management'] = False
    RiskManagementOrchestrator = None

# Risk Unified
try:
    from trading_bot.risk_unified import UnifiedRiskOrchestrator
    _AVAILABLE['risk_unified'] = True
except Exception as e:
    _AVAILABLE['risk_unified'] = False
    UnifiedRiskOrchestrator = None

# Schemas
try:
    from trading_bot.schemas import SchemaManager
    _AVAILABLE['schemas'] = True
except Exception as e:
    _AVAILABLE['schemas'] = False
    SchemaManager = None

# Security (full)
try:
    from trading_bot.security import SecurityOrchestrator
    _AVAILABLE['security'] = True
except Exception as e:
    _AVAILABLE['security'] = False
    SecurityOrchestrator = None

# Self Concepts
try:
    from trading_bot.self_concepts import SelfConceptsOrchestrator
    _AVAILABLE['self_concepts'] = True
except Exception as e:
    _AVAILABLE['self_concepts'] = False
    SelfConceptsOrchestrator = None

# Signals (full)
try:
    from trading_bot.signals import SignalOrchestrator
    _AVAILABLE['signals'] = True
except Exception as e:
    _AVAILABLE['signals'] = False
    SignalOrchestrator = None

# Simulation
try:
    from trading_bot.simulation import SimulationOrchestrator
    _AVAILABLE['simulation'] = True
except Exception as e:
    _AVAILABLE['simulation'] = False
    SimulationOrchestrator = None

# Skills
try:
    from trading_bot.skills import SkillsOrchestrator
    _AVAILABLE['skills'] = True
except Exception as e:
    _AVAILABLE['skills'] = False
    SkillsOrchestrator = None

# Social
try:
    from trading_bot.social import SocialOrchestrator
    _AVAILABLE['social'] = True
except Exception as e:
    _AVAILABLE['social'] = False
    SocialOrchestrator = None

# Strategies (full)
try:
    from trading_bot.strategies import StrategiesOrchestrator
    _AVAILABLE['strategies'] = True
except Exception as e:
    _AVAILABLE['strategies'] = False
    StrategiesOrchestrator = None

# Surveillance
try:
    from trading_bot.surveillance import SurveillanceOrchestrator
    _AVAILABLE['surveillance'] = True
except Exception as e:
    _AVAILABLE['surveillance'] = False
    SurveillanceOrchestrator = None

# System
try:
    from trading_bot.system import SystemOrchestrator
    _AVAILABLE['system'] = True
except Exception as e:
    _AVAILABLE['system'] = False
    SystemOrchestrator = None

# TAMIC
try:
    from trading_bot.tamic import TAMICOrchestrator
    _AVAILABLE['tamic'] = True
except Exception as e:
    _AVAILABLE['tamic'] = False
    TAMICOrchestrator = None

# Testing
try:
    from trading_bot.testing import TestingOrchestrator
    _AVAILABLE['testing'] = True
except Exception as e:
    _AVAILABLE['testing'] = False
    TestingOrchestrator = None

# Tools
try:
    from trading_bot.tools import ToolsOrchestrator
    _AVAILABLE['tools'] = True
except Exception as e:
    _AVAILABLE['tools'] = False
    ToolsOrchestrator = None

# Trade Journal
try:
    from trading_bot.trade_journal import TradeJournalOrchestrator
    _AVAILABLE['trade_journal'] = True
except Exception as e:
    _AVAILABLE['trade_journal'] = False
    TradeJournalOrchestrator = None

# Trading
try:
    from trading_bot.trading import TradingOrchestrator
    _AVAILABLE['trading'] = True
except Exception as e:
    _AVAILABLE['trading'] = False
    TradingOrchestrator = None

# Trading Calendar
try:
    from trading_bot.trading_calendar import TradingCalendarOrchestrator
    _AVAILABLE['trading_calendar'] = True
except Exception as e:
    _AVAILABLE['trading_calendar'] = False
    TradingCalendarOrchestrator = None

# Ultimate Approval
try:
    from trading_bot.ultimate_approval import UltimateApprovalOrchestrator
    _AVAILABLE['ultimate_approval'] = True
except Exception as e:
    _AVAILABLE['ultimate_approval'] = False
    UltimateApprovalOrchestrator = None

# Ultimate Architecture
try:
    from trading_bot.ultimate_architecture import UltimateArchitectureOrchestrator
    _AVAILABLE['ultimate_architecture'] = True
except Exception as e:
    _AVAILABLE['ultimate_architecture'] = False
    UltimateArchitectureOrchestrator = None

# Ultimate Production
try:
    from trading_bot.ultimate_production import UltimateProductionOrchestrator
    _AVAILABLE['ultimate_production'] = True
except Exception as e:
    _AVAILABLE['ultimate_production'] = False
    UltimateProductionOrchestrator = None

# Unified Approval
try:
    from trading_bot.unified_approval import UnifiedApprovalOrchestrator
    _AVAILABLE['unified_approval'] = True
except Exception as e:
    _AVAILABLE['unified_approval'] = False
    UnifiedApprovalOrchestrator = None

# Unified Architecture
try:
    from trading_bot.unified_architecture import UnifiedArchitectureOrchestrator
    _AVAILABLE['unified_architecture'] = True
except Exception as e:
    _AVAILABLE['unified_architecture'] = False
    UnifiedArchitectureOrchestrator = None

# Upgrades
try:
    from trading_bot.upgrades import UpgradesOrchestrator
    _AVAILABLE['upgrades'] = True
except Exception as e:
    _AVAILABLE['upgrades'] = False
    UpgradesOrchestrator = None

# Utils
try:
    from trading_bot.utils import UtilsOrchestrator
    _AVAILABLE['utils'] = True
except Exception as e:
    _AVAILABLE['utils'] = False
    UtilsOrchestrator = None

# Validation
try:
    from trading_bot.validation import ValidationOrchestrator
    _AVAILABLE['validation'] = True
except Exception as e:
    _AVAILABLE['validation'] = False
    ValidationOrchestrator = None

# Verification
try:
    from trading_bot.verification import VerificationOrchestrator
    _AVAILABLE['verification'] = True
except Exception as e:
    _AVAILABLE['verification'] = False
    VerificationOrchestrator = None

# Visualization
try:
    from trading_bot.visualization import VisualizationOrchestrator
    _AVAILABLE['visualization'] = True
except Exception as e:
    _AVAILABLE['visualization'] = False
    VisualizationOrchestrator = None

# Voice Assistant
try:
    from trading_bot.voice_assistant import VoiceAssistantOrchestrator
    _AVAILABLE['voice_assistant'] = True
except Exception as e:
    _AVAILABLE['voice_assistant'] = False
    VoiceAssistantOrchestrator = None

# Wealth
try:
    from trading_bot.wealth import WealthOrchestrator
    _AVAILABLE['wealth'] = True
except Exception as e:
    _AVAILABLE['wealth'] = False
    WealthOrchestrator = None
    
# Core Orchestrator
try:
    from trading_bot.core import CoreOrchestrator
    _AVAILABLE['core_orchestrator'] = True
except Exception as e:
    _AVAILABLE['core_orchestrator'] = False
    CoreOrchestrator = None

# Analysis Orchestrator
try:
    from trading_bot.analysis import AnalysisOrchestrator
    _AVAILABLE['analysis_orchestrator'] = True
except Exception as e:
    _AVAILABLE['analysis_orchestrator'] = False
    AnalysisOrchestrator = None

# ML and AI modules
try:
    from trading_bot.ml.transformer_model import TransformerPricePredictor
    _AVAILABLE['transformer'] = True
except Exception:
    _AVAILABLE['transformer'] = False
    TransformerPricePredictor = None

try:
    from trading_bot.ml.rl_agent import PPOAgent
    _AVAILABLE['rl'] = True
except Exception:
    _AVAILABLE['rl'] = False
    PPOAgent = None

try:
    from trading_bot.ml.market_regime_classifier import MarketRegimeClassifier
    _AVAILABLE['market_regime'] = True
except Exception:
    _AVAILABLE['market_regime'] = False
    MarketRegimeClassifier = None

# Sentiment and news
try:
    from trading_bot.sentiment.sentiment_analyzer import SentimentAnalyzer
    _AVAILABLE['sentiment'] = True
except Exception:
    _AVAILABLE['sentiment'] = False
    SentimentAnalyzer = None

# Connectivity modules
try:
    from trading_bot.connectivity.api_client import APIClient
    _AVAILABLE['api_client'] = True
except Exception:
    _AVAILABLE['api_client'] = False
    APIClient = None

try:
    from trading_bot.connectivity.websocket_client import WebsocketClient
    _AVAILABLE['websocket'] = True
except Exception:
    _AVAILABLE['websocket'] = False
    WebsocketClient = None

try:
    from trading_bot.connectivity.web_scraper import WebScraper
    _AVAILABLE['web_scraper'] = True
except Exception:
    _AVAILABLE['web_scraper'] = False
    WebScraper = None

# Orchestrator and advanced systems
try:
    from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator
    _AVAILABLE['orchestrator'] = True
except Exception:
    _AVAILABLE['orchestrator'] = False
    MasterOrchestrator = None

try:
    from trading_bot.opportunity_scanner.scanner_manager import ScannerManager
    _AVAILABLE['scanners'] = True
except Exception:
    _AVAILABLE['scanners'] = False
    ScannerManager = None

try:
    from trading_bot.exit_strategies.exit_manager import ExitManager
    _AVAILABLE['advanced_exits'] = True
except Exception:
    _AVAILABLE['advanced_exits'] = False
    ExitManager = None

try:
    from trading_bot.adaptive_systems.adaptive_manager import AdaptiveManager
    _AVAILABLE['adaptive'] = True
except Exception:
    _AVAILABLE['adaptive'] = False
    AdaptiveManager = None

# Dashboard
try:
    from trading_bot.dashboard.dashboard_server import DashboardServer
    _AVAILABLE['dashboard'] = True
except Exception:
    _AVAILABLE['dashboard'] = False
    DashboardServer = None

# Backtesting
try:
    from trading_bot.backtesting.backtesting_engine import BacktestingEngine
    _AVAILABLE['backtesting'] = True
except Exception:
    _AVAILABLE['backtesting'] = False
    BacktestingEngine = None

# ============================================================================
# ADDITIONAL MODULE IMPORTS (COMPLETE INTEGRATION)
# ============================================================================

# Advanced AI
try:
    from trading_bot.advanced_ai import AdvancedAIOrchestrator
    _AVAILABLE['advanced_ai'] = True
except Exception:
    _AVAILABLE['advanced_ai'] = False
    AdvancedAIOrchestrator = None

# Alternative Data
try:
    from trading_bot.alternative_data import AlternativeDataOrchestrator
    _AVAILABLE['alternative_data'] = True
except Exception:
    _AVAILABLE['alternative_data'] = False
    AlternativeDataOrchestrator = None

# Brokers (multi-broker support)
try:
    from trading_bot.brokers import BrokersOrchestrator
    _AVAILABLE['brokers'] = True
except Exception:
    _AVAILABLE['brokers'] = False
    BrokersOrchestrator = None

# Config Manager
try:
    from trading_bot.config import ConfigManager
    _AVAILABLE['config_manager'] = True
except Exception:
    _AVAILABLE['config_manager'] = False
    ConfigManager = None

# Connectivity
try:
    from trading_bot.connectivity import ConnectivityOrchestrator
    _AVAILABLE['connectivity'] = True
except Exception:
    _AVAILABLE['connectivity'] = False
    ConnectivityOrchestrator = None

# Data Sources
try:
    from trading_bot.data_sources import DataSourcesOrchestrator
    _AVAILABLE['data_sources'] = True
except Exception:
    _AVAILABLE['data_sources'] = False
    DataSourcesOrchestrator = None

# Elite System
try:
    from trading_bot.elite_system import EliteSystemOrchestrator
    _AVAILABLE['elite_system'] = True
except Exception:
    _AVAILABLE['elite_system'] = False
    EliteSystemOrchestrator = None

# Hivemind
try:
    from trading_bot.hivemind import HivemindOrchestrator
    _AVAILABLE['hivemind'] = True
except Exception:
    _AVAILABLE['hivemind'] = False
    HivemindOrchestrator = None

# Infrastructure
try:
    from trading_bot.infrastructure import InfrastructureOrchestrator
    _AVAILABLE['infrastructure'] = True
except Exception:
    _AVAILABLE['infrastructure'] = False
    InfrastructureOrchestrator = None

# Institutional
try:
    from trading_bot.institutional import InstitutionalOrchestrator as InstitutionalFull
    _AVAILABLE['institutional'] = True
except Exception:
    _AVAILABLE['institutional'] = False
    InstitutionalFull = None

# Integration
try:
    from trading_bot.integration import IntegrationOrchestrator
    _AVAILABLE['integration'] = True
except Exception:
    _AVAILABLE['integration'] = False
    IntegrationOrchestrator = None

# Integrations
try:
    from trading_bot.integrations import IntegrationsOrchestrator
    _AVAILABLE['integrations'] = True
except Exception:
    _AVAILABLE['integrations'] = False
    IntegrationsOrchestrator = None

# Models
try:
    from trading_bot.models import ModelsOrchestrator
    _AVAILABLE['models'] = True
except Exception:
    _AVAILABLE['models'] = False
    ModelsOrchestrator = None

# Perplexity Trading
try:
    from trading_bot.perplexity_trading import PerplexityTradingOrchestrator
    _AVAILABLE['perplexity_trading'] = True
except Exception:
    _AVAILABLE['perplexity_trading'] = False
    PerplexityTradingOrchestrator = None

# Position (full)
try:
    from trading_bot.position import PositionOrchestrator
    _AVAILABLE['position'] = True
except Exception:
    _AVAILABLE['position'] = False
    PositionOrchestrator = None

# Quant Analysis
try:
    from trading_bot.quant_analysis import QuantAnalysisOrchestrator
    _AVAILABLE['quant_analysis'] = True
except Exception:
    _AVAILABLE['quant_analysis'] = False
    QuantAnalysisOrchestrator = None

# Reporting
try:
    from trading_bot.reporting import ReportingOrchestrator
    _AVAILABLE['reporting'] = True
except Exception:
    _AVAILABLE['reporting'] = False
    ReportingOrchestrator = None

# Self Assembly AI
try:
    from trading_bot.self_assembly_ai import SelfAssemblyOrchestrator
    _AVAILABLE['self_assembly_ai'] = True
except Exception:
    _AVAILABLE['self_assembly_ai'] = False
    SelfAssemblyOrchestrator = None

# Services
try:
    from trading_bot.services import ServicesOrchestrator
    _AVAILABLE['services'] = True
except Exception:
    _AVAILABLE['services'] = False
    ServicesOrchestrator = None

# Strategy (full)
try:
    from trading_bot.strategy import StrategyOrchestrator
    _AVAILABLE['strategy_full'] = True
except Exception:
    _AVAILABLE['strategy_full'] = False
    StrategyOrchestrator = None

# Superpowerful AI
try:
    from trading_bot.superpowerful_ai import SuperpowerfulOrchestrator
    _AVAILABLE['superpowerful_ai'] = True
except Exception:
    _AVAILABLE['superpowerful_ai'] = False
    SuperpowerfulOrchestrator = None

# Ultimate Bot
try:
    from trading_bot.ultimate_bot import UltimateBotOrchestrator
    _AVAILABLE['ultimate_bot'] = True
except Exception:
    _AVAILABLE['ultimate_bot'] = False
    UltimateBotOrchestrator = None

# AI (base module)
try:
    from trading_bot.ai import AIOrchestrator
    _AVAILABLE['ai'] = True
except Exception:
    _AVAILABLE['ai'] = False
    AIOrchestrator = None

# Analytics (full)
try:
    from trading_bot.analytics import AnalyticsOrchestrator
    _AVAILABLE['analytics'] = True
except Exception:
    _AVAILABLE['analytics'] = False
    AnalyticsOrchestrator = None

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Advanced Algorithmic Trading Bot for MetaTrader 5 (Individual File Integration)",
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
        help="MT5 timeframe key (M1, M5, M15, H1,â€¦). Defaults to M15.",
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
        "--integrate-all-modules",
        action="store_true",
        help="Instantiate all available imported orchestrator/manager/system modules.",
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
    
    # ============================================================================
    # LAYER 1 INTEGRATION ARGUMENTS
    # ============================================================================
    parser.add_argument(
        "--use-all-systems",
        action="store_true",
        help="Enable all Layer 1 core systems (recommended for maximum performance).",
        default=False,
    )
    parser.add_argument(
        "--use-elite-ai",
        action="store_true",
        help="Use Elite AI System for advanced signal generation.",
        default=False,
    )
    parser.add_argument(
        "--analysis-depth",
        choices=["quick", "standard", "deep", "exhaustive"],
        default="standard",
        help="Elite AI analysis depth (quick=1-2s, standard=5-10s, deep=30-60s, exhaustive=2-5min).",
    )
    parser.add_argument(
        "--use-market-intelligence",
        action="store_true",
        help="Use Market Intelligence for Wyckoff, liquidity, and order flow analysis.",
        default=False,
    )
    parser.add_argument(
        "--use-complete-system",
        action="store_true",
        help="Use 100%% Complete System for full trading pipeline.",
        default=False,
    )
    parser.add_argument(
        "--use-enhanced-risk",
        action="store_true",
        help="Use Enhanced Risk Management with advanced position sizing.",
        default=False,
    )
    parser.add_argument(
        "--use-smart-execution",
        action="store_true",
        help="Use Smart Execution with TWAP/VWAP/Smart routing.",
        default=False,
    )
    parser.add_argument(
        "--use-performance-analytics",
        action="store_true",
        help="Use Real-time Performance Analytics.",
        default=False,
    )
    parser.add_argument(
        "--use-hedge-fund-safety",
        action="store_true",
        help="Use Hedge Fund Safety system for institutional-grade protection.",
        default=False,
    )
    parser.add_argument(
        "--start-background-services",
        action="store_true",
        help="Start background services (Market Student, Evolution, Diagnostics).",
        default=False,
    )

    return parser.parse_args(argv)


# ============================================================================
# MULTI-SYMBOL TRADING FUNCTIONALITY
# ============================================================================

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
        if MT5Interface is None:
            raise ImportError("MT5Interface not available")
        mt5i = MT5Interface()
        
        # Create strategy engine
        strategy_engine = self._create_strategy_engine(symbol, args, mt5i)
        
        # Create risk manager
        if RiskManager is None:
            raise ImportError("RiskManager not available")
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
        if args.use_ml and MLStrategyEngine:
            # MLStrategyEngine accepts: use_price_prediction, use_pattern_recognition, use_sentiment
            return MLStrategyEngine(
                mt5i,
                symbol=symbol,
                use_price_prediction=True,
                use_pattern_recognition=True,
                use_sentiment=getattr(args, 'sentiment_analysis', False)
            )
        elif StrategyEngine:
            return StrategyEngine(mt5i, symbol=symbol)
        else:
            raise ImportError("No strategy engine available")
    
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _select_executor(mt5i, risk_manager, mode, execution_algo, emotional_tracker=None):
    """Select appropriate executor based on mode and algorithm."""
    base_executor = None
    
    if mode == "paper" and PaperExecutor:
        base_executor = PaperExecutor(mt5i, risk_manager)
        logger.info("Using PaperExecutor for paper trading mode")
    elif mode == "live" and LiveExecutor:
        base_executor = LiveExecutor(mt5i, risk_manager)
        logger.info("Using LiveExecutor for live trading mode")
    elif mode == "smoke" and PaperExecutor:
        # Smoke test mode - use paper executor for connectivity testing only
        logger.info("Using smoke test mode - paper executor for connectivity testing only")
        base_executor = PaperExecutor(mt5i, risk_manager)
    elif PaperExecutor:
        # Fallback to paper executor if available
        logger.warning(f"Mode '{mode}' not available, falling back to PaperExecutor")
        base_executor = PaperExecutor(mt5i, risk_manager)
    else:
        # No executor available - this is a critical error
        error_msg = f"No executor available for mode '{mode}'. PaperExecutor={PaperExecutor}, LiveExecutor={LiveExecutor}"
        logger.error(error_msg)
        raise ImportError(error_msg)
    
    # Apply execution algorithm wrapper if specified
    if execution_algo == "twap" and TWAPExecutor:
        logger.info("Using TWAP execution algorithm")
        return TWAPExecutor(base_executor)
    elif execution_algo == "vwap" and VWAPExecutor:
        logger.info("Using VWAP execution algorithm")
        return VWAPExecutor(base_executor)
    elif execution_algo == "smart" and SmartOrderRouter:
        logger.info("Using Smart Order Router (standalone mode)")
        # SmartOrderRouter is standalone, doesn't wrap an executor
        # Return base executor for now (SmartOrderRouter needs separate integration)
        return base_executor
    else:
        logger.info("Using default execution")
        return base_executor


_AUTO_INTEGRATION_SUFFIXES = (
    "Orchestrator",
    "Manager",
    "System",
    "Integrator",
    "Engine",
    "Core",
    "Analyzer",
    "Scanner",
    "Validator",
)

_AUTO_INTEGRATION_SKIP = {
    "MT5Interface",
    "StrategyEngine",
    "MLStrategyEngine",
    "PaperExecutor",
    "LiveExecutor",
    "TWAPExecutor",
    "VWAPExecutor",
    "SmartOrderRouter",
    "RiskManager",
    "PerformanceAnalytics",
    "EmotionalStateTracker",
    "APIClient",
    "WebsocketClient",
    "WebScraper",
    "DashboardServer",
    "BacktestingEngine",
    "ScannerManager",
    "ExitManager",
    "AdaptiveManager",
}


def _to_snake_case(name: str) -> str:
    """Convert CamelCase name to snake_case key."""
    output = []
    for idx, char in enumerate(name):
        if idx > 0 and char.isupper() and not name[idx - 1].isupper():
            output.append("_")
        output.append(char.lower())
    return "".join(output)


def _is_auto_integration_candidate(name: str, obj: Any) -> bool:
    """Return True if a global class is suitable for auto-integration."""
    if name in _AUTO_INTEGRATION_SKIP or obj is None:
        return False
    if not inspect.isclass(obj):
        return False
    module_name = getattr(obj, "__module__", "")
    if not module_name.startswith("trading_bot"):
        return False
    if not any(name.endswith(suffix) for suffix in _AUTO_INTEGRATION_SUFFIXES):
        return False
    return True


def _construct_with_fallbacks(component_cls: Any, config: Dict[str, Any]) -> tuple[Optional[Any], Optional[str], Optional[Exception]]:
    """Construct a component using common constructor signatures."""
    attempts = [
        ("no_args", lambda: component_cls()),
        ("config_positional", lambda: component_cls(config)),
        ("config_kw", lambda: component_cls(config=config)),
        ("settings_kw", lambda: component_cls(settings=config)),
        ("workspace_and_config", lambda: component_cls(workspace_path=".", config=config)),
        ("workspace_only", lambda: component_cls(workspace_path=".")),
        ("path_positional", lambda: component_cls(".")),
    ]

    last_error: Optional[Exception] = None
    for attempt_name, factory in attempts:
        try:
            return factory(), attempt_name, None
        except Exception as exc:
            last_error = exc

    return None, None, last_error


def initialize_all_imported_modules(config: Dict[str, Any], existing_systems: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Instantiate all imported trading_bot modules that look like runtime systems.

    This enables practical "all modules integrated" behavior in main.py without
    hard-coding every constructor signature.
    """
    integrated: Dict[str, Any] = {}
    existing_systems = existing_systems or {}
    existing_types = {type(value) for value in existing_systems.values() if value is not None}
    seen_types = set(existing_types)

    candidates = [
        (name, obj)
        for name, obj in globals().items()
        if _is_auto_integration_candidate(name, obj)
    ]

    failures = 0
    for class_name, component_cls in sorted(candidates, key=lambda item: item[0].lower()):
        if component_cls in seen_types:
            continue

        instance, init_mode, error = _construct_with_fallbacks(component_cls, config)
        if instance is None:
            failures += 1
            logger.debug("Auto-integration skipped for {}: {}", class_name, error)
            continue

        seen_types.add(component_cls)
        module_key = _to_snake_case(class_name)
        integrated[module_key] = instance
        logger.info("Auto-integrated module: {} ({})", module_key, init_mode)

    logger.info(
        "Auto-module integration complete: {} initialized, {} skipped",
        len(integrated),
        failures,
    )
    return integrated


async def shutdown_integrated_modules(modules: Dict[str, Any], label: str = "module") -> None:
    """Best-effort shutdown for integrated module instances."""
    for module_key, instance in modules.items():
        if instance is None:
            continue

        for method_name in ("stop", "shutdown", "close"):
            method = getattr(instance, method_name, None)
            if not callable(method):
                continue

            try:
                result = method()
                if asyncio.iscoroutine(result):
                    await result
                logger.info("Stopped {}: {}", label, module_key)
            except Exception as exc:
                logger.warning("Failed to stop {} {}: {}", label, module_key, exc)
            break


def _initialize_connectivity(api_source, websocket_feed, news_scraping, cache_dir, api_keys_file):
    """Initialize internet connectivity components using individual file imports."""
    components = {}
    
    # Initialize cache manager if available
    if _AVAILABLE.get('api_client', False) and APIClient:
        try:
            # Use APIClient as cache manager if no dedicated cache manager
            components['cache_manager'] = APIClient(base_url="https://cache.local", api_name="cache")
            logger.info("Cache manager initialized")
        except Exception as e:
            logger.warning(f"Could not initialize cache manager: {e}")
    
    # Initialize API client based on source
    if api_source and _AVAILABLE.get('api_client', False) and APIClient:
        try:
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
    if websocket_feed and _AVAILABLE.get('websocket', False) and WebsocketClient:
        try:
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
    if news_scraping and _AVAILABLE.get('web_scraper', False) and WebScraper:
        try:
            components['web_scraper'] = WebScraper()
            logger.info("Web scraper initialized for news scraping")
        except Exception as e:
            logger.warning(f"Could not initialize web scraper: {e}")
    
    logger.info(f"Connectivity initialized with {len(components)} components: {list(components.keys())}")
    return components


# ============================================================================
# INTEGRATED SYSTEMS CLASS - UNIFIED MODULE ORCHESTRATION
# ============================================================================

class IntegratedSystems:
    """
    Unified container for all trading bot modules.
    Organizes modules by category with proper initialization order and lifecycle management.
    
    Architecture:
    - Safety Layer (IMMUTABLE): Has veto power over all decisions
    - Intelligence Layer: AI/ML systems for signal generation
    - Execution Layer: Order execution and management
    - Monitoring Layer: Performance and health monitoring
    - Learning Layer: Continuous improvement systems
    - Advanced Layer: Optional advanced features
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
        
        # Module categories
        self.safety = {}        # Safety systems (veto power)
        self.intelligence = {}  # AI/ML systems
        self.execution = {}     # Execution systems
        self.monitoring = {}    # Monitoring systems
        self.learning = {}      # Learning systems
        self.market = {}        # Market analysis systems
        self.advanced = {}      # Advanced features
        self.infrastructure = {} # Infrastructure systems
        
        # Initialization status tracking
        self._init_status = {}
        self._init_errors = {}
        
        # Event bus for inter-module communication
        self._event_subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self._event_subscribers:
            self._event_subscribers[event_type] = []
        self._event_subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._event_subscribers:
            self._event_subscribers[event_type] = [
                cb for cb in self._event_subscribers[event_type] if cb != callback
            ]
    
    async def publish(self, event_type: str, data: Dict = None, source: str = None):
        """Publish an event to all subscribers."""
        event = {
            'type': event_type,
            'data': data or {},
            'source': source or 'unknown',
            'timestamp': datetime.now().isoformat(),
        }
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Notify subscribers
        if event_type in self._event_subscribers:
            for callback in self._event_subscribers[event_type]:
                try:
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.debug(f"Event callback error for {event_type}: {e}")
        
        # Also notify wildcard subscribers
        if '*' in self._event_subscribers:
            for callback in self._event_subscribers['*']:
                try:
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.debug(f"Wildcard callback error: {e}")
    
    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Dict]:
        """Get event history, optionally filtered by type."""
        if event_type:
            filtered = [e for e in self._event_history if e['type'] == event_type]
        else:
            filtered = self._event_history
        return filtered[-limit:]
    
    async def initialize_all(self, args=None) -> Dict[str, int]:
        """
        Initialize all modules in priority order.
        Returns dict with counts of initialized modules per category.
        """
        logger.info("=" * 70)
        logger.info("INITIALIZING INTEGRATED SYSTEMS")
        logger.info("=" * 70)
        
        counts = {}
        
        # 1. SAFETY LAYER (FIRST - Has veto power)
        counts['safety'] = await self._init_safety(args)
        
        # 2. INFRASTRUCTURE LAYER
        counts['infrastructure'] = await self._init_infrastructure(args)
        
        # 3. MARKET ANALYSIS LAYER
        counts['market'] = await self._init_market(args)
        
        # 4. INTELLIGENCE LAYER
        counts['intelligence'] = await self._init_intelligence(args)
        
        # 5. EXECUTION LAYER
        counts['execution'] = await self._init_execution(args)
        
        # 6. MONITORING LAYER
        counts['monitoring'] = await self._init_monitoring(args)
        
        # 7. LEARNING LAYER
        counts['learning'] = await self._init_learning(args)
        
        # 8. ADVANCED FEATURES (Optional)
        counts['advanced'] = await self._init_advanced(args)
        
        self.initialized = True
        
        total = sum(counts.values())
        logger.info("=" * 70)
        logger.info(f"INTEGRATED SYSTEMS INITIALIZED: {total} modules active")
        for category, count in counts.items():
            logger.info(f"  {category}: {count} modules")
        logger.info("=" * 70)
        
        return counts
    
    async def _init_safety(self, args=None) -> int:
        """Initialize safety systems (IMMUTABLE - has veto power)."""
        logger.info("[SAFETY] Initializing safety layer...")
        count = 0
        
        # Reality Gates - Pre-execution checks
        if _AVAILABLE.get('reality_gates') and RealityGateOrchestrator:
            try:
                self.safety['reality_gates'] = RealityGateOrchestrator()
                logger.info("  [OK] Reality Gates")
                count += 1
            except Exception as e:
                self._init_errors['reality_gates'] = str(e)
                logger.warning(f"  [FAIL] Reality Gates: {e}")
        
        # Safety Orchestrator - Circuit breakers
        if _AVAILABLE.get('safety') and SafetyOrchestrator:
            try:
                self.safety['safety_orchestrator'] = SafetyOrchestrator()
                logger.info("  [OK] Safety Orchestrator")
                count += 1
            except Exception as e:
                self._init_errors['safety_orchestrator'] = str(e)
                logger.warning(f"  [FAIL] Safety Orchestrator: {e}")
        
        # Hedge Fund Safety - Institutional-grade protection
        if _AVAILABLE.get('hedge_fund_safety') and HedgeFundSafetyOrchestrator:
            try:
                self.safety['hedge_fund_safety'] = HedgeFundSafetyOrchestrator()
                logger.info("  [OK] Hedge Fund Safety")
                count += 1
            except Exception as e:
                self._init_errors['hedge_fund_safety'] = str(e)
                logger.warning(f"  [FAIL] Hedge Fund Safety: {e}")
        
        # Stealth Safety - Low-profile operation
        if _AVAILABLE.get('stealth_safety') and StealthSafetyManager:
            try:
                self.safety['stealth_safety'] = StealthSafetyManager()
                logger.info("  [OK] Stealth Safety")
                count += 1
            except Exception as e:
                self._init_errors['stealth_safety'] = str(e)
                logger.warning(f"  [FAIL] Stealth Safety: {e}")
        
        # Complete Risk System
        if _AVAILABLE.get('enhanced_risk') and CompleteRiskSystem:
            try:
                self.safety['risk_system'] = CompleteRiskSystem()
                logger.info("  [OK] Complete Risk System")
                count += 1
            except Exception as e:
                self._init_errors['risk_system'] = str(e)
                logger.warning(f"  [FAIL] Complete Risk System: {e}")
        
        # Compliance Manager
        if _AVAILABLE.get('compliance') and ComplianceManager:
            try:
                self.safety['compliance'] = ComplianceManager()
                logger.info("  [OK] Compliance Manager")
                count += 1
            except Exception as e:
                self._init_errors['compliance'] = str(e)
                logger.warning(f"  [FAIL] Compliance Manager: {e}")
        
        logger.info(f"[SAFETY] {count} safety systems initialized")
        return count
    
    async def _init_infrastructure(self, args=None) -> int:
        """Initialize infrastructure systems."""
        logger.info("[INFRASTRUCTURE] Initializing infrastructure layer...")
        count = 0
        
        # Database Manager
        if _AVAILABLE.get('database') and DatabaseManager:
            try:
                self.infrastructure['database'] = DatabaseManager()
                logger.info("  [OK] Database Manager")
                count += 1
            except Exception as e:
                self._init_errors['database'] = str(e)
                logger.warning(f"  [FAIL] Database Manager: {e}")
        
        # Event Pipeline
        if _AVAILABLE.get('event_pipeline') and EventPipeline:
            try:
                self.infrastructure['event_pipeline'] = EventPipeline()
                logger.info("  [OK] Event Pipeline")
                count += 1
            except Exception as e:
                self._init_errors['event_pipeline'] = str(e)
                logger.warning(f"  [FAIL] Event Pipeline: {e}")
        
        # Ingestion Orchestrator
        if _AVAILABLE.get('ingestion') and IngestionOrchestrator:
            try:
                self.infrastructure['ingestion'] = IngestionOrchestrator(self.config)
                logger.info("  [OK] Ingestion Orchestrator")
                count += 1
            except Exception as e:
                self._init_errors['ingestion'] = str(e)
                logger.warning(f"  [FAIL] Ingestion Orchestrator: {e}")
        
        # Streaming Manager
        if _AVAILABLE.get('streaming') and StreamingManager:
            try:
                self.infrastructure['streaming'] = StreamingManager(self.config)
                logger.info("  [OK] Streaming Manager")
                count += 1
            except Exception as e:
                self._init_errors['streaming'] = str(e)
                logger.warning(f"  [FAIL] Streaming Manager: {e}")
        
        # Data Feeds Manager
        if _AVAILABLE.get('data_feeds') and DataFeedManager:
            try:
                self.infrastructure['data_feeds'] = DataFeedManager(self.config)
                logger.info("  [OK] Data Feeds Manager")
                count += 1
            except Exception as e:
                self._init_errors['data_feeds'] = str(e)
                logger.warning(f"  [FAIL] Data Feeds Manager: {e}")
        
        logger.info(f"[INFRASTRUCTURE] {count} infrastructure systems initialized")
        return count
    
    async def _init_market(self, args=None) -> int:
        """Initialize market analysis systems."""
        logger.info("[MARKET] Initializing market analysis layer...")
        count = 0
        
        # Market Intelligence (DeepChart)
        if _AVAILABLE.get('deepchart') and MarketIntelligenceOrchestrator:
            try:
                self.market['deepchart'] = MarketIntelligenceOrchestrator()
                logger.info("  [OK] DeepChart Market Intelligence")
                count += 1
            except Exception as e:
                self._init_errors['deepchart'] = str(e)
                logger.warning(f"  [FAIL] DeepChart: {e}")
        
        # MSOS (Market Survival Operating System)
        if _AVAILABLE.get('msos') and MSOSOrchestrator:
            try:
                self.market['msos'] = MSOSOrchestrator()
                logger.info("  [OK] MSOS")
                count += 1
            except Exception as e:
                self._init_errors['msos'] = str(e)
                logger.warning(f"  [FAIL] MSOS: {e}")
        
        # Systems AI
        if _AVAILABLE.get('systems_ai') and SystemsAIOrchestrator:
            try:
                self.market['systems_ai'] = SystemsAIOrchestrator()
                logger.info("  [OK] Systems AI")
                count += 1
            except Exception as e:
                self._init_errors['systems_ai'] = str(e)
                logger.warning(f"  [FAIL] Systems AI: {e}")
        
        # Market Data Monitor
        if _AVAILABLE.get('market_intelligence') and MarketDataMonitor:
            try:
                self.market['market_monitor'] = MarketDataMonitor()
                logger.info("  [OK] Market Data Monitor")
                count += 1
            except Exception as e:
                self._init_errors['market_monitor'] = str(e)
                logger.warning(f"  [FAIL] Market Data Monitor: {e}")
        
        # World Model
        if _AVAILABLE.get('world_model') and WorldModel:
            try:
                self.market['world_model'] = WorldModel(self.config)
                logger.info("  [OK] World Model")
                count += 1
            except Exception as e:
                self._init_errors['world_model'] = str(e)
                logger.warning(f"  [FAIL] World Model: {e}")
        
        logger.info(f"[MARKET] {count} market analysis systems initialized")
        return count
    
    async def _init_intelligence(self, args=None) -> int:
        """Initialize AI/ML intelligence systems."""
        logger.info("[INTELLIGENCE] Initializing intelligence layer...")
        count = 0
        
        # Unified AI Brain (PRIMARY)
        if _AVAILABLE.get('unified_brain') and UnifiedAIBrain:
            try:
                brain_config = BrainConfig(mode=self.config.get('mode', 'paper')) if BrainConfig else {}
                self.intelligence['unified_brain'] = UnifiedAIBrain(brain_config)
                logger.info("  [OK] Unified AI Brain (PRIMARY)")
                count += 1
            except Exception as e:
                self._init_errors['unified_brain'] = str(e)
                logger.warning(f"  [FAIL] Unified AI Brain: {e}")
        
        # Elite Trading Orchestrator
        if _AVAILABLE.get('elite_ai') and EliteTradingOrchestrator:
            try:
                self.intelligence['elite_ai'] = EliteTradingOrchestrator(self.config)
                logger.info("  [OK] Elite AI")
                count += 1
            except Exception as e:
                self._init_errors['elite_ai'] = str(e)
                logger.warning(f"  [FAIL] Elite AI: {e}")
        
        # Cognitive Orchestrator
        if _AVAILABLE.get('cognitive') and CognitiveOrchestrator:
            try:
                self.intelligence['cognitive'] = CognitiveOrchestrator(self.config)
                logger.info("  [OK] Cognitive Architecture")
                count += 1
            except Exception as e:
                self._init_errors['cognitive'] = str(e)
                logger.warning(f"  [FAIL] Cognitive Architecture: {e}")
        
        # Brain Orchestrator
        if _AVAILABLE.get('brain') and BrainOrchestrator:
            try:
                self.intelligence['brain'] = BrainOrchestrator(self.config)
                logger.info("  [OK] Brain Orchestrator")
                count += 1
            except Exception as e:
                self._init_errors['brain'] = str(e)
                logger.warning(f"  [FAIL] Brain Orchestrator: {e}")
        
        # Alpha Engine
        if _AVAILABLE.get('alpha_engine') and AlphaEngine:
            try:
                self.intelligence['alpha_engine'] = AlphaEngine(self.config)
                logger.info("  [OK] Alpha Engine")
                count += 1
            except Exception as e:
                self._init_errors['alpha_engine'] = str(e)
                logger.warning(f"  [FAIL] Alpha Engine: {e}")
        
        # Decision Layer
        if _AVAILABLE.get('decision_layer') and DecisionLayerOrchestrator:
            try:
                self.intelligence['decision_layer'] = DecisionLayerOrchestrator(self.config)
                logger.info("  [OK] Decision Layer")
                count += 1
            except Exception as e:
                self._init_errors['decision_layer'] = str(e)
                logger.warning(f"  [FAIL] Decision Layer: {e}")
        
        # AI Core
        if _AVAILABLE.get('ai_core') and AICoreOrchestrator:
            try:
                self.intelligence['ai_core'] = AICoreOrchestrator(self.config)
                logger.info("  [OK] AI Core")
                count += 1
            except Exception as e:
                self._init_errors['ai_core'] = str(e)
                logger.warning(f"  [FAIL] AI Core: {e}")
        
        # Profit Maximizer
        if _AVAILABLE.get('profit_maximizer') and ProfitMaximizer:
            try:
                self.intelligence['profit_maximizer'] = ProfitMaximizer(self.config)
                logger.info("  [OK] Profit Maximizer")
                count += 1
            except Exception as e:
                self._init_errors['profit_maximizer'] = str(e)
                logger.warning(f"  [FAIL] Profit Maximizer: {e}")
        
        # AlphaAlgo Core
        if _AVAILABLE.get('alphaalgo_core') and AlphaAlgoCore:
            try:
                self.intelligence['alphaalgo_core'] = AlphaAlgoCore()
                logger.info("  [OK] AlphaAlgo Core")
                count += 1
            except Exception as e:
                self._init_errors['alphaalgo_core'] = str(e)
                logger.warning(f"  [FAIL] AlphaAlgo Core: {e}")
        
        # AAMIS V3
        if _AVAILABLE.get('aamis_v3') and AAMISOrchestrator:
            try:
                self.intelligence['aamis_v3'] = AAMISOrchestrator()
                logger.info("  [OK] AAMIS V3")
                count += 1
            except Exception as e:
                self._init_errors['aamis_v3'] = str(e)
                logger.warning(f"  [FAIL] AAMIS V3: {e}")
        
        # Intelligent Delegation
        if _AVAILABLE.get('intelligent_delegation') and DelegationOrchestrator:
            try:
                self.intelligence['delegation'] = DelegationOrchestrator()
                logger.info("  [OK] Intelligent Delegation")
                count += 1
            except Exception as e:
                self._init_errors['delegation'] = str(e)
                logger.warning(f"  [FAIL] Intelligent Delegation: {e}")
        
        logger.info(f"[INTELLIGENCE] {count} intelligence systems initialized")
        return count
    
    async def _init_execution(self, args=None) -> int:
        """Initialize execution systems."""
        logger.info("[EXECUTION] Initializing execution layer...")
        count = 0
        
        # Complete Execution System
        if _AVAILABLE.get('smart_execution') and CompleteExecutionSystem:
            try:
                self.execution['complete_execution'] = CompleteExecutionSystem()
                logger.info("  [OK] Complete Execution System")
                count += 1
            except Exception as e:
                self._init_errors['complete_execution'] = str(e)
                logger.warning(f"  [FAIL] Complete Execution System: {e}")
        
        # Trading Engine
        if _AVAILABLE.get('trading_engine') and TradingEngine:
            try:
                self.execution['trading_engine'] = TradingEngine()
                logger.info("  [OK] Trading Engine")
                count += 1
            except Exception as e:
                self._init_errors['trading_engine'] = str(e)
                logger.warning(f"  [FAIL] Trading Engine: {e}")
        
        # Master Trading System (100% Complete)
        if _AVAILABLE.get('complete_system') and MasterTradingSystem:
            try:
                self.execution['master_trading'] = MasterTradingSystem()
                logger.info("  [OK] Master Trading System")
                count += 1
            except Exception as e:
                self._init_errors['master_trading'] = str(e)
                logger.warning(f"  [FAIL] Master Trading System: {e}")
        
        # Position Manager
        if _AVAILABLE.get('position_manager') and PositionManager:
            try:
                self.execution['position_manager'] = PositionManager()
                logger.info("  [OK] Position Manager")
                count += 1
            except Exception as e:
                self._init_errors['position_manager'] = str(e)
                logger.warning(f"  [FAIL] Position Manager: {e}")
        
        logger.info(f"[EXECUTION] {count} execution systems initialized")
        return count
    
    async def _init_monitoring(self, args=None) -> int:
        """Initialize monitoring systems."""
        logger.info("[MONITORING] Initializing monitoring layer...")
        count = 0
        
        # Performance System
        if _AVAILABLE.get('performance_analytics') and CompletePerformanceSystem:
            try:
                self.monitoring['performance'] = CompletePerformanceSystem()
                logger.info("  [OK] Performance System")
                count += 1
            except Exception as e:
                self._init_errors['performance'] = str(e)
                logger.warning(f"  [FAIL] Performance System: {e}")
        
        # Monitoring Orchestrator
        if _AVAILABLE.get('monitoring') and MonitoringOrchestrator:
            try:
                self.monitoring['monitoring'] = MonitoringOrchestrator(self.config)
                logger.info("  [OK] Monitoring Orchestrator")
                count += 1
            except Exception as e:
                self._init_errors['monitoring'] = str(e)
                logger.warning(f"  [FAIL] Monitoring Orchestrator: {e}")
        
        # System Health Manager
        if _AVAILABLE.get('system_health') and SystemHealthManager:
            try:
                self.monitoring['system_health'] = SystemHealthManager()
                logger.info("  [OK] System Health Manager")
                count += 1
            except Exception as e:
                self._init_errors['system_health'] = str(e)
                logger.warning(f"  [FAIL] System Health Manager: {e}")
        
        # System Supervisor
        if _AVAILABLE.get('system_supervisor') and SystemSupervisor:
            try:
                self.monitoring['supervisor'] = SystemSupervisor(self.config)
                logger.info("  [OK] System Supervisor")
                count += 1
            except Exception as e:
                self._init_errors['supervisor'] = str(e)
                logger.warning(f"  [FAIL] System Supervisor: {e}")
        
        # Event Monitoring
        if _AVAILABLE.get('event_monitoring') and EventMonitor:
            try:
                self.monitoring['event_monitor'] = EventMonitor()
                logger.info("  [OK] Event Monitor")
                count += 1
            except Exception as e:
                self._init_errors['event_monitor'] = str(e)
                logger.warning(f"  [FAIL] Event Monitor: {e}")
        
        # Observability Manager
        if _AVAILABLE.get('observability') and ObservabilityManager:
            try:
                self.monitoring['observability'] = ObservabilityManager()
                logger.info("  [OK] Observability Manager")
                count += 1
            except Exception as e:
                self._init_errors['observability'] = str(e)
                logger.warning(f"  [FAIL] Observability Manager: {e}")
        
        # Telemetry Manager
        if _AVAILABLE.get('telemetry') and TelemetryManager:
            try:
                self.monitoring['telemetry'] = TelemetryManager()
                logger.info("  [OK] Telemetry Manager")
                count += 1
            except Exception as e:
                self._init_errors['telemetry'] = str(e)
                logger.warning(f"  [FAIL] Telemetry Manager: {e}")
        
        # Alert Manager
        if _AVAILABLE.get('alerts') and AlertManager:
            try:
                self.monitoring['alerts'] = AlertManager(self.config)
                logger.info("  [OK] Alert Manager")
                count += 1
            except Exception as e:
                self._init_errors['alerts'] = str(e)
                logger.warning(f"  [FAIL] Alert Manager: {e}")
        
        # Notification Manager
        if _AVAILABLE.get('notifications') and NotificationManager:
            try:
                self.monitoring['notifications'] = NotificationManager(self.config)
                logger.info("  [OK] Notification Manager")
                count += 1
            except Exception as e:
                self._init_errors['notifications'] = str(e)
                logger.warning(f"  [FAIL] Notification Manager: {e}")
        
        # Audit Manager
        if _AVAILABLE.get('audit') and AuditManager:
            try:
                self.monitoring['audit'] = AuditManager()
                logger.info("  [OK] Audit Manager")
                count += 1
            except Exception as e:
                self._init_errors['audit'] = str(e)
                logger.warning(f"  [FAIL] Audit Manager: {e}")
        
        # Governance Manager
        if _AVAILABLE.get('governance') and GovernanceManager:
            try:
                self.monitoring['governance'] = GovernanceManager()
                logger.info("  [OK] Governance Manager")
                count += 1
            except Exception as e:
                self._init_errors['governance'] = str(e)
                logger.warning(f"  [FAIL] Governance Manager: {e}")
        
        logger.info(f"[MONITORING] {count} monitoring systems initialized")
        return count
    
    async def _init_learning(self, args=None) -> int:
        """Initialize learning and self-improvement systems."""
        logger.info("[LEARNING] Initializing learning layer...")
        count = 0
        
        # Self-Diagnostic
        if _AVAILABLE.get('self_diagnostic') and SelfManager:
            try:
                self.learning['self_diagnostic'] = SelfManager()
                logger.info("  [OK] Self-Diagnostic")
                count += 1
            except Exception as e:
                self._init_errors['self_diagnostic'] = str(e)
                logger.warning(f"  [FAIL] Self-Diagnostic: {e}")
        
        # Market Student
        if _AVAILABLE.get('market_student') and MarketStudentOrchestrator:
            try:
                self.learning['market_student'] = MarketStudentOrchestrator(self.config)
                logger.info("  [OK] Market Student")
                count += 1
            except Exception as e:
                self._init_errors['market_student'] = str(e)
                logger.warning(f"  [FAIL] Market Student: {e}")
        
        # Eternal Evolution
        if _AVAILABLE.get('eternal_evolution') and EternalEvolutionOrchestrator:
            try:
                self.learning['eternal_evolution'] = EternalEvolutionOrchestrator(self.config)
                logger.info("  [OK] Eternal Evolution")
                count += 1
            except Exception as e:
                self._init_errors['eternal_evolution'] = str(e)
                logger.warning(f"  [FAIL] Eternal Evolution: {e}")
        
        # Self-Improvement Engine
        if _AVAILABLE.get('self_improvement') and SelfImprovementEngine:
            try:
                self.learning['self_improvement'] = SelfImprovementEngine()
                logger.info("  [OK] Self-Improvement Engine")
                count += 1
            except Exception as e:
                self._init_errors['self_improvement'] = str(e)
                logger.warning(f"  [FAIL] Self-Improvement Engine: {e}")
        
        # Self-Learning Engine
        if _AVAILABLE.get('self_learning') and SelfLearningEngine:
            try:
                self.learning['self_learning'] = SelfLearningEngine()
                logger.info("  [OK] Self-Learning Engine")
                count += 1
            except Exception as e:
                self._init_errors['self_learning'] = str(e)
                logger.warning(f"  [FAIL] Self-Learning Engine: {e}")
        
        # Self-Healing Orchestrator
        if _AVAILABLE.get('self_healing') and SelfHealingOrchestrator:
            try:
                self.learning['self_healing'] = SelfHealingOrchestrator(self.config)
                logger.info("  [OK] Self-Healing")
                count += 1
            except Exception as e:
                self._init_errors['self_healing'] = str(e)
                logger.warning(f"  [FAIL] Self-Healing: {e}")
        
        # Recursive Improvement
        if _AVAILABLE.get('recursive_improvement') and RecursiveImprovementEngine:
            try:
                self.learning['recursive_improvement'] = RecursiveImprovementEngine()
                logger.info("  [OK] Recursive Improvement")
                count += 1
            except Exception as e:
                self._init_errors['recursive_improvement'] = str(e)
                logger.warning(f"  [FAIL] Recursive Improvement: {e}")
        
        # Alpha Research
        if _AVAILABLE.get('alpha_research') and AlphaResearchOrchestrator:
            try:
                self.learning['alpha_research'] = AlphaResearchOrchestrator()
                logger.info("  [OK] Alpha Research")
                count += 1
            except Exception as e:
                self._init_errors['alpha_research'] = str(e)
                logger.warning(f"  [FAIL] Alpha Research: {e}")
        
        # Adversarial Curriculum
        if _AVAILABLE.get('adversarial_curriculum') and CurriculumOrchestrator:
            try:
                self.learning['adversarial_curriculum'] = CurriculumOrchestrator()
                logger.info("  [OK] Adversarial Curriculum")
                count += 1
            except Exception as e:
                self._init_errors['adversarial_curriculum'] = str(e)
                logger.warning(f"  [FAIL] Adversarial Curriculum: {e}")
        
        # Offline RL Continuous Learning
        if _AVAILABLE.get('offline_rl_continuous') and ContinuousLearningOrchestrator:
            try:
                self.learning['offline_rl'] = ContinuousLearningOrchestrator()
                logger.info("  [OK] Offline RL Continuous Learning")
                count += 1
            except Exception as e:
                self._init_errors['offline_rl'] = str(e)
                logger.warning(f"  [FAIL] Offline RL: {e}")
        
        logger.info(f"[LEARNING] {count} learning systems initialized")
        return count
    
    async def _init_advanced(self, args=None) -> int:
        """Initialize advanced feature systems."""
        logger.info("[ADVANCED] Initializing advanced features...")
        count = 0
        
        # Quantum Optimizer
        if _AVAILABLE.get('quantum') and QuantumOptimizer:
            try:
                self.advanced['quantum'] = QuantumOptimizer(self.config)
                logger.info("  [OK] Quantum Optimizer")
                count += 1
            except Exception as e:
                self._init_errors['quantum'] = str(e)
                logger.warning(f"  [FAIL] Quantum Optimizer: {e}")
        
        # Blockchain Validator
        if _AVAILABLE.get('blockchain') and BlockchainValidator:
            try:
                self.advanced['blockchain'] = BlockchainValidator()
                logger.info("  [OK] Blockchain Validator")
                count += 1
            except Exception as e:
                self._init_errors['blockchain'] = str(e)
                logger.warning(f"  [FAIL] Blockchain Validator: {e}")
        
        # Arbitrage Scanner
        if _AVAILABLE.get('arbitrage') and ArbitrageScanner:
            try:
                self.advanced['arbitrage'] = ArbitrageScanner(self.config)
                logger.info("  [OK] Arbitrage Scanner")
                count += 1
            except Exception as e:
                self._init_errors['arbitrage'] = str(e)
                logger.warning(f"  [FAIL] Arbitrage Scanner: {e}")
        
        # Portfolio Manager
        if _AVAILABLE.get('portfolio') and PortfolioManager:
            try:
                self.advanced['portfolio'] = PortfolioManager(self.config)
                logger.info("  [OK] Portfolio Manager")
                count += 1
            except Exception as e:
                self._init_errors['portfolio'] = str(e)
                logger.warning(f"  [FAIL] Portfolio Manager: {e}")
        
        # Multimodal Analyzer
        if _AVAILABLE.get('multimodal') and MultimodalAnalyzer:
            try:
                self.advanced['multimodal'] = MultimodalAnalyzer(self.config)
                logger.info("  [OK] Multimodal Analyzer")
                count += 1
            except Exception as e:
                self._init_errors['multimodal'] = str(e)
                logger.warning(f"  [FAIL] Multimodal Analyzer: {e}")
        
        # Autonomous Orchestrator
        if _AVAILABLE.get('autonomous') and AutonomousOrchestrator:
            try:
                self.advanced['autonomous'] = AutonomousOrchestrator(self.config)
                logger.info("  [OK] Autonomous Orchestrator")
                count += 1
            except Exception as e:
                self._init_errors['autonomous'] = str(e)
                logger.warning(f"  [FAIL] Autonomous Orchestrator: {e}")
        
        # Sentient Core
        if _AVAILABLE.get('sentient_core') and SentientOrchestrator:
            try:
                self.advanced['sentient_core'] = SentientOrchestrator(self.config)
                logger.info("  [OK] Sentient Core")
                count += 1
            except Exception as e:
                self._init_errors['sentient_core'] = str(e)
                logger.warning(f"  [FAIL] Sentient Core: {e}")
        
        # Hedge Fund Orchestrator
        if _AVAILABLE.get('hedge_fund') and HedgeFundOrchestrator:
            try:
                self.advanced['hedge_fund'] = HedgeFundOrchestrator()
                logger.info("  [OK] Hedge Fund Orchestrator")
                count += 1
            except Exception as e:
                self._init_errors['hedge_fund'] = str(e)
                logger.warning(f"  [FAIL] Hedge Fund Orchestrator: {e}")
        
        # AlphaAlgo V2
        if _AVAILABLE.get('alphaalgo_v2') and AlphaAlgoV2Orchestrator:
            try:
                self.advanced['alphaalgo_v2'] = AlphaAlgoV2Orchestrator()
                logger.info("  [OK] AlphaAlgo V2")
                count += 1
            except Exception as e:
                self._init_errors['alphaalgo_v2'] = str(e)
                logger.warning(f"  [FAIL] AlphaAlgo V2: {e}")
        
        # AlphaAlgo Institutional
        if _AVAILABLE.get('alphaalgo_institutional') and InstitutionalOrchestrator:
            try:
                self.advanced['alphaalgo_institutional'] = InstitutionalOrchestrator()
                logger.info("  [OK] AlphaAlgo Institutional")
                count += 1
            except Exception as e:
                self._init_errors['alphaalgo_institutional'] = str(e)
                logger.warning(f"  [FAIL] AlphaAlgo Institutional: {e}")
        
        # Advanced AI
        if _AVAILABLE.get('advanced_ai') and AdvancedAIOrchestrator:
            try:
                self.advanced['advanced_ai'] = AdvancedAIOrchestrator()
                logger.info("  [OK] Advanced AI")
                count += 1
            except Exception as e:
                self._init_errors['advanced_ai'] = str(e)
                logger.warning(f"  [FAIL] Advanced AI: {e}")
        
        # Alternative Data
        if _AVAILABLE.get('alternative_data') and AlternativeDataOrchestrator:
            try:
                self.advanced['alternative_data'] = AlternativeDataOrchestrator()
                logger.info("  [OK] Alternative Data")
                count += 1
            except Exception as e:
                self._init_errors['alternative_data'] = str(e)
                logger.warning(f"  [FAIL] Alternative Data: {e}")
        
        # Hivemind
        if _AVAILABLE.get('hivemind') and HivemindOrchestrator:
            try:
                self.advanced['hivemind'] = HivemindOrchestrator(self.config)
                logger.info("  [OK] Hivemind")
                count += 1
            except Exception as e:
                self._init_errors['hivemind'] = str(e)
                logger.warning(f"  [FAIL] Hivemind: {e}")
        
        # Perplexity Trading
        if _AVAILABLE.get('perplexity_trading') and PerplexityTradingOrchestrator:
            try:
                self.advanced['perplexity_trading'] = PerplexityTradingOrchestrator()
                logger.info("  [OK] Perplexity Trading")
                count += 1
            except Exception as e:
                self._init_errors['perplexity_trading'] = str(e)
                logger.warning(f"  [FAIL] Perplexity Trading: {e}")
        
        # Self Assembly AI
        if _AVAILABLE.get('self_assembly_ai') and SelfAssemblyOrchestrator:
            try:
                self.advanced['self_assembly_ai'] = SelfAssemblyOrchestrator()
                logger.info("  [OK] Self Assembly AI")
                count += 1
            except Exception as e:
                self._init_errors['self_assembly_ai'] = str(e)
                logger.warning(f"  [FAIL] Self Assembly AI: {e}")
        
        # Superpowerful AI
        if _AVAILABLE.get('superpowerful_ai') and SuperpowerfulOrchestrator:
            try:
                self.advanced['superpowerful_ai'] = SuperpowerfulOrchestrator(self.config)
                logger.info("  [OK] Superpowerful AI")
                count += 1
            except Exception as e:
                self._init_errors['superpowerful_ai'] = str(e)
                logger.warning(f"  [FAIL] Superpowerful AI: {e}")
        
        # Ultimate Bot
        if _AVAILABLE.get('ultimate_bot') and UltimateBotOrchestrator:
            try:
                self.advanced['ultimate_bot'] = UltimateBotOrchestrator()
                logger.info("  [OK] Ultimate Bot")
                count += 1
            except Exception as e:
                self._init_errors['ultimate_bot'] = str(e)
                logger.warning(f"  [FAIL] Ultimate Bot: {e}")
        
        # Elite System
        if _AVAILABLE.get('elite_system') and EliteSystemOrchestrator:
            try:
                self.advanced['elite_system'] = EliteSystemOrchestrator()
                logger.info("  [OK] Elite System")
                count += 1
            except Exception as e:
                self._init_errors['elite_system'] = str(e)
                logger.warning(f"  [FAIL] Elite System: {e}")
        
        logger.info(f"[ADVANCED] {count} advanced features initialized")
        return count
    
    def validate_trade(self, symbol: str, direction: int, size: float, 
                       signal_data: Dict = None) -> tuple[bool, str, Dict]:
        """
        Validate a trade through all safety systems.
        Returns (is_valid, reason, adjustments).
        Safety layer has VETO power.
        """
        adjustments = {}
        
        # 1. Reality Gates check
        if 'reality_gates' in self.safety and self.safety['reality_gates']:
            try:
                rg = self.safety['reality_gates']
                if hasattr(rg, 'validate'):
                    result = rg.validate(symbol, direction, size)
                    if isinstance(result, dict) and not result.get('valid', True):
                        return False, f"Reality Gates: {result.get('reason', 'Blocked')}", {}
                    elif result is False:
                        return False, "Reality Gates: Trade blocked", {}
            except Exception as e:
                logger.warning(f"Reality Gates validation error: {e}")
        
        # 2. Safety Orchestrator check
        if 'safety_orchestrator' in self.safety and self.safety['safety_orchestrator']:
            try:
                so = self.safety['safety_orchestrator']
                if hasattr(so, 'validate_trade'):
                    result = so.validate_trade(symbol, direction, size)
                    if isinstance(result, dict) and not result.get('valid', True):
                        return False, f"Safety: {result.get('reason', 'Blocked')}", {}
                    elif result is False:
                        return False, "Safety: Trade blocked", {}
            except Exception as e:
                logger.warning(f"Safety validation error: {e}")
        
        # 3. Hedge Fund Safety check
        if 'hedge_fund_safety' in self.safety and self.safety['hedge_fund_safety']:
            try:
                hfs = self.safety['hedge_fund_safety']
                if hasattr(hfs, 'validate_trade'):
                    result = hfs.validate_trade(symbol, direction, size, signal_data or {})
                    if isinstance(result, tuple):
                        is_valid, reason = result[0], result[1] if len(result) > 1 else ""
                        if not is_valid:
                            return False, f"Hedge Fund Safety: {reason}", {}
                    elif isinstance(result, dict) and not result.get('valid', True):
                        return False, f"Hedge Fund Safety: {result.get('reason', 'Blocked')}", {}
            except Exception as e:
                logger.warning(f"Hedge Fund Safety validation error: {e}")
        
        # 4. Risk System check
        if 'risk_system' in self.safety and self.safety['risk_system']:
            try:
                rs = self.safety['risk_system']
                if hasattr(rs, 'check_risk'):
                    result = rs.check_risk(symbol, direction, size)
                    if isinstance(result, dict):
                        if not result.get('valid', True):
                            return False, f"Risk: {result.get('reason', 'Blocked')}", {}
                        if 'adjusted_size' in result:
                            adjustments['size'] = result['adjusted_size']
            except Exception as e:
                logger.warning(f"Risk validation error: {e}")
        
        # 5. Compliance check
        if 'compliance' in self.safety and self.safety['compliance']:
            try:
                cm = self.safety['compliance']
                if hasattr(cm, 'check_compliance'):
                    result = cm.check_compliance(symbol, direction, size)
                    if isinstance(result, dict) and not result.get('compliant', True):
                        return False, f"Compliance: {result.get('reason', 'Blocked')}", {}
            except Exception as e:
                logger.warning(f"Compliance validation error: {e}")
        
        return True, "Trade validated", adjustments
    
    async def enhance_signal(self, signal: Dict, market_data: Any = None) -> Dict:
        """
        Enhance a trading signal through intelligence systems.
        Returns enhanced signal with additional insights.
        """
        enhanced = signal.copy()
        
        # 1. Alpha Engine enhancement
        if 'alpha_engine' in self.intelligence and self.intelligence['alpha_engine']:
            try:
                ae = self.intelligence['alpha_engine']
                if hasattr(ae, 'enhance_signal'):
                    result = ae.enhance_signal(signal, market_data)
                    if isinstance(result, dict):
                        enhanced.update(result)
            except Exception as e:
                logger.debug(f"Alpha Engine enhancement error: {e}")
        
        # 2. Decision Layer enhancement
        if 'decision_layer' in self.intelligence and self.intelligence['decision_layer']:
            try:
                dl = self.intelligence['decision_layer']
                if hasattr(dl, 'evaluate'):
                    result = dl.evaluate(signal)
                    if isinstance(result, dict):
                        enhanced['decision_layer_score'] = result.get('score', 0.5)
            except Exception as e:
                logger.debug(f"Decision Layer enhancement error: {e}")
        
        # 3. Profit Maximizer enhancement
        if 'profit_maximizer' in self.intelligence and self.intelligence['profit_maximizer']:
            try:
                pm = self.intelligence['profit_maximizer']
                if hasattr(pm, 'optimize_entry'):
                    result = pm.optimize_entry(signal)
                    if isinstance(result, dict):
                        enhanced.update(result)
            except Exception as e:
                logger.debug(f"Profit Maximizer enhancement error: {e}")
        
        return enhanced
    
    async def get_market_intelligence(self, symbol: str, market_data: Any = None) -> Dict:
        """Get market intelligence from all market analysis systems."""
        intelligence = {}
        
        # DeepChart
        if 'deepchart' in self.market and self.market['deepchart']:
            try:
                dc = self.market['deepchart']
                if hasattr(dc, 'analyze'):
                    intelligence['deepchart'] = dc.analyze(symbol, market_data)
            except Exception as e:
                logger.debug(f"DeepChart analysis error: {e}")
        
        # MSOS
        if 'msos' in self.market and self.market['msos']:
            try:
                msos = self.market['msos']
                if hasattr(msos, 'evaluate'):
                    intelligence['msos'] = msos.evaluate(symbol, market_data)
            except Exception as e:
                logger.debug(f"MSOS analysis error: {e}")
        
        # Systems AI
        if 'systems_ai' in self.market and self.market['systems_ai']:
            try:
                sai = self.market['systems_ai']
                if hasattr(sai, 'analyze'):
                    intelligence['systems_ai'] = sai.analyze(symbol, market_data)
            except Exception as e:
                logger.debug(f"Systems AI analysis error: {e}")
        
        return intelligence
    
    async def shutdown(self):
        """Gracefully shutdown all systems."""
        logger.info("Shutting down integrated systems...")
        
        all_systems = [
            ('safety', self.safety),
            ('intelligence', self.intelligence),
            ('execution', self.execution),
            ('monitoring', self.monitoring),
            ('learning', self.learning),
            ('market', self.market),
            ('advanced', self.advanced),
            ('infrastructure', self.infrastructure),
        ]
        
        for category, systems in all_systems:
            for name, instance in systems.items():
                if instance is None:
                    continue
                
                for method_name in ('stop', 'shutdown', 'close', 'cleanup'):
                    method = getattr(instance, method_name, None)
                    if callable(method):
                        try:
                            result = method()
                            if asyncio.iscoroutine(result):
                                await result
                            logger.debug(f"Stopped {category}/{name}")
                        except Exception as e:
                            logger.warning(f"Error stopping {category}/{name}: {e}")
                        break
        
        logger.info("Integrated systems shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all integrated systems."""
        status = {
            'initialized': self.initialized,
            'categories': {},
            'errors': self._init_errors,
        }
        
        for category, systems in [
            ('safety', self.safety),
            ('intelligence', self.intelligence),
            ('execution', self.execution),
            ('monitoring', self.monitoring),
            ('learning', self.learning),
            ('market', self.market),
            ('advanced', self.advanced),
            ('infrastructure', self.infrastructure),
        ]:
            status['categories'][category] = {
                'count': len([s for s in systems.values() if s is not None]),
                'systems': list(systems.keys()),
            }
        
        return status


# ============================================================================
# LAYER 1 CORE SYSTEMS INITIALIZATION
# ============================================================================

async def initialize_core_systems(args, config: Dict) -> Dict[str, Any]:
    """Initialize all Layer 1 core systems based on command-line arguments."""
    systems = {}
    
    # If --use-all-systems, enable everything
    if args.use_all_systems:
        args.use_elite_ai = True
        args.use_market_intelligence = True
        args.use_complete_system = True
        args.use_enhanced_risk = True
        args.use_smart_execution = True
        args.use_performance_analytics = True
        args.use_hedge_fund_safety = True
    
    logger.info("=" * 70)
    logger.info("INITIALIZING LAYER 1 CORE SYSTEMS")
    logger.info("=" * 70)
    
    # Elite AI System
    if args.use_elite_ai and _AVAILABLE.get('elite_ai'):
        try:
            systems['elite_ai'] = EliteTradingOrchestrator(config)
            logger.info("âœ“ Elite AI System initialized")
        except Exception as e:
            logger.error(f"âœ— Elite AI initialization failed: {e}")
            systems['elite_ai'] = None
    else:
        systems['elite_ai'] = None
    
    # Market Intelligence
    if args.use_market_intelligence and _AVAILABLE.get('market_intelligence'):
        try:
            systems['market_monitor'] = MarketDataMonitor()
            logger.info("âœ“ Market Intelligence initialized")
        except Exception as e:
            logger.error(f"âœ— Market Intelligence initialization failed: {e}")
            systems['market_monitor'] = None
    else:
        systems['market_monitor'] = None
    
    # 100% Complete System
    if args.use_complete_system and _AVAILABLE.get('complete_system'):
        try:
            systems['complete_system'] = MasterTradingSystem()
            logger.info("âœ“ 100% Complete System initialized")
        except Exception as e:
            logger.error(f"âœ— Complete System initialization failed: {e}")
            systems['complete_system'] = None
    else:
        systems['complete_system'] = None
    
    # Enhanced Risk Management
    if args.use_enhanced_risk and _AVAILABLE.get('enhanced_risk'):
        try:
            systems['risk_system'] = CompleteRiskSystem()
            logger.info("âœ“ Enhanced Risk System initialized")
        except Exception as e:
            logger.error(f"âœ— Risk System initialization failed: {e}")
            systems['risk_system'] = None
    else:
        systems['risk_system'] = None
    
    # Smart Execution
    if args.use_smart_execution and _AVAILABLE.get('smart_execution'):
        try:
            systems['execution_system'] = CompleteExecutionSystem()
            logger.info("âœ“ Smart Execution System initialized")
        except Exception as e:
            logger.error(f"âœ— Execution System initialization failed: {e}")
            systems['execution_system'] = None
    else:
        systems['execution_system'] = None
    
    # Performance Analytics
    if args.use_performance_analytics and _AVAILABLE.get('performance_analytics'):
        try:
            systems['performance_system'] = CompletePerformanceSystem()
            logger.info("âœ“ Performance Analytics initialized")
        except Exception as e:
            logger.error(f"âœ— Performance Analytics initialization failed: {e}")
            systems['performance_system'] = None
    else:
        systems['performance_system'] = None
    
    # Hedge Fund Safety
    if args.use_hedge_fund_safety and _AVAILABLE.get('hedge_fund_safety'):
        try:
            systems['safety_system'] = HedgeFundSafetyOrchestrator()
            logger.info("âœ“ Hedge Fund Safety initialized")
        except Exception as e:
            logger.error(f"âœ— Hedge Fund Safety initialization failed: {e}")
            systems['safety_system'] = None
    else:
        systems['safety_system'] = None
    
    # Self-Diagnostic (always try to initialize for health monitoring)
    if _AVAILABLE.get('self_diagnostic'):
        try:
            systems['self_diagnostic'] = SelfManager()
            logger.info("âœ“ Self-Diagnostic initialized")
        except Exception as e:
            logger.warning(f"Self-Diagnostic initialization failed: {e}")
            systems['self_diagnostic'] = None
    
    logger.info("=" * 70)
    active_count = sum(1 for v in systems.values() if v is not None)
    logger.info(f"LAYER 1 INITIALIZATION COMPLETE: {active_count} systems active")
    logger.info("=" * 70)
    
    return systems


async def start_background_services_async(config: Dict) -> Any:
    """Start background services (Layer 2) in async context."""
    try:
        from background_services import BackgroundServicesManager
        
        manager = BackgroundServicesManager(config)
        await manager.start_all()
        logger.info("âœ“ Background services started")
        return manager
    except Exception as e:
        logger.error(f"Failed to start background services: {e}")
        return None


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

# Restore stderr after all imports are complete
sys.stderr = _original_stderr

@profile_function("INFO")
async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # ------------------------------------------------------------------
    # Initialise logging
    # ------------------------------------------------------------------
    init_logger(level=args.log_level)

    # ------------------------------------------------------------------
    # Report module availability
    # ------------------------------------------------------------------
    available_count = sum(1 for available in _AVAILABLE.values() if available)
    total_count = len(_AVAILABLE)
    logger.info("Individual module integration: {}/{} modules loaded successfully ({:.1f}%)", 
               available_count, total_count, (available_count/total_count*100) if total_count > 0 else 0)
    
    # Show available modules
    for module_name, available in _AVAILABLE.items():
        status = "âœ“" if available else "âœ—"
        logger.info("  {}: {}", status, module_name)
    
    # Show core module status
    core_modules = {
        'MT5Interface': MT5Interface is not None,
        'StrategyEngine': StrategyEngine is not None,
        'MLStrategyEngine': MLStrategyEngine is not None,
        'PaperExecutor': PaperExecutor is not None,
        'LiveExecutor': LiveExecutor is not None,
        'RiskManager': RiskManager is not None,
    }
    logger.info("Core modules available: {}/{}", sum(core_modules.values()), len(core_modules))

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
    logger.info("  - Individual file integration: ACTIVE")
    logger.info("=" * 70)
    
    # ------------------------------------------------------------------
    # Handle integrated systems modes
    # ------------------------------------------------------------------
    auto_integrated_modules: Dict[str, Any] = {}
    connectivity_components: Dict[str, Any] = {}
    
    # Check if full integration is requested
    if args.full_integration:
        args.orchestrator = True
        args.enable_scanners = True
        args.advanced_exits = True
        args.adaptive = True
        args.use_all_systems = True
        args.integrate_all_modules = True
        logger.info("Full integration mode enabled - activating all systems")
    
    # ------------------------------------------------------------------
    # MASTER INTEGRATION ENGINE  — single authority startup
    # ------------------------------------------------------------------
    _master_engine = None
    if _AVAILABLE.get('master_integration_engine') and get_engine is not None:
        try:
            logger.info("=" * 60)
            logger.info("MASTER INTEGRATION ENGINE: Starting world-class integration")
            logger.info("=" * 60)
            _engine_cfg = EngineConfig(
                fail_fast_on_tier_a=False,   # graceful in main; don't abort waves
                block_direct_impact_without_risk=True,
                health_check_interval_s=60.0,
                startup_wave_order=[0, 1, 4, 5, 2, 3, 6, 7],
            )
            _master_engine = get_engine(config=_engine_cfg)

            # Register modules already loaded above as legacy adapters
            _legacy_map = [
                # (instance_or_class, svc_name, layer, tier, cap_impact, rollback)
                (MSOSOrchestrator,          'msos',              4, 'A', 'direct',   'emergency'),
                (SafetyOrchestrator,        'safety_manager',    4, 'A', 'direct',   'emergency'),
                (RealityGateOrchestrator,   'reality_gates',     4, 'A', 'direct',   'emergency'),
                (HedgeFundSafetyOrchestrator,'hedge_fund_safety',4, 'A', 'direct',   'emergency'),
                (RiskManager,               'risk_manager',      4, 'A', 'direct',   'emergency'),
                (MarketIntelligenceOrchestrator,'market_intelligence',3,'A','indirect','degrade'),
                (MarketDataMonitor,         'market_data_monitor',1,'A','indirect',   'degrade'),
                (AlphaEngine,               'alpha_engine',      3, 'A', 'indirect', 'degrade'),
                (SystemsAIOrchestrator,     'systems_ai',        3, 'B', 'indirect', 'degrade'),
                (EliteTradingOrchestrator,  'elite_ai_system',   3, 'B', 'indirect', 'degrade'),
                (DecisionLayerOrchestrator, 'decision_layer',    3, 'A', 'direct',   'isolate'),
                (BrainOrchestrator,         'brain_core',        2, 'B', 'indirect', 'degrade'),
                (AICoreOrchestrator,        'ai_core',           2, 'A', 'indirect', 'degrade'),
                (PortfolioManager,          'portfolio_manager', 5, 'A', 'direct',   'isolate'),
                (PositionManager,           'position_manager',  5, 'A', 'direct',   'isolate'),
                (ComplianceManager,         'compliance_monitor',6, 'A', 'none',     'safe_disable'),
                (AuditManager,             'audit_logger',       6, 'A', 'none',     'safe_disable'),
                (GovernanceManager,         'governance_manager',6, 'A', 'none',     'safe_disable'),
                (EventPipeline,             'event_bus',         7, 'A', 'indirect', 'degrade'),
                (SystemSupervisor,          'system_supervisor', 7, 'A', 'indirect', 'degrade'),
                (MonitoringOrchestrator,    'monitoring',        0, 'C', 'none',     'safe_disable'),
                (TelemetryManager,          'telemetry',         0, 'C', 'none',     'safe_disable'),
                (SelfManager,               'self_diagnostic',   0, 'B', 'none',     'degrade'),
                (DatabaseManager,           'database_manager',  1, 'A', 'none',     'isolate'),
                (IngestionOrchestrator,     'ingestion_pipeline',1, 'A', 'indirect', 'degrade'),
                (DataFeedManager,           'data_feeds',        1, 'A', 'indirect', 'degrade'),
                (StreamingManager,          'data_stream',       1, 'A', 'indirect', 'degrade'),
            ]
            for (cls_or_inst, svc_name, lyr, tier, cap, rb) in _legacy_map:
                if cls_or_inst is None:
                    _master_engine.register_stub(svc_name, reason='import_failed')
                    continue
                try:
                    inst = cls_or_inst() if isinstance(cls_or_inst, type) else cls_or_inst
                    _master_engine.register_legacy(
                        instance=inst,
                        service_name=svc_name,
                        layer=lyr,
                        tier=tier,
                        capital_impact=cap,
                        rollback_class=rb,
                    )
                except Exception as _reg_err:
                    logger.warning(f"Engine: could not register {svc_name}: {_reg_err}")
                    _master_engine.register_stub(svc_name, reason=str(_reg_err)[:80])

            # Start all waves
            _engine_results = await _master_engine.start_all()
            _eng_health = _master_engine.engine_health_report()
            logger.info(
                f"ENGINE: {_eng_health['running']}/{_eng_health['total_registered']} "
                f"services running | degraded={_eng_health['degraded']} "
                f"error={_eng_health['error']}"
            )
            _AVAILABLE['master_integration_engine_running'] = _eng_health['running'] > 0
        except Exception as _engine_startup_err:
            logger.warning(f"MasterIntegrationEngine startup error: {_engine_startup_err}")
            _master_engine = None

    # ------------------------------------------------------------------
    # Initialize INTEGRATED SYSTEMS (All modules unified)
    # ------------------------------------------------------------------
    integrated_systems = None
    if args.full_integration or args.use_all_systems or args.integrate_all_modules:
        logger.info("Initializing INTEGRATED SYSTEMS (unified module orchestration)...")
        integrated_systems = IntegratedSystems(PROFITABILITY_CONFIG)
        await integrated_systems.initialize_all(args)
        
        # Show integration status
        status = integrated_systems.get_status()
        logger.info("Integrated Systems Status:")
        for category, info in status['categories'].items():
            logger.info(f"  {category}: {info['count']} modules - {info['systems']}")
    
    # ------------------------------------------------------------------
    # Initialize Layer 1 Core Systems (legacy path)
    # ------------------------------------------------------------------
    core_systems = await initialize_core_systems(args, PROFITABILITY_CONFIG)
    
    # ------------------------------------------------------------------
    # Start Background Services (Layer 2) if requested
    # ------------------------------------------------------------------
    background_manager = None
    if args.start_background_services:
        background_manager = await start_background_services_async(PROFITABILITY_CONFIG)
        if background_manager:
            logger.info("[OK] Background services running in parallel")
    
    # ------------------------------------------------------------------
    # Initialize internet/connectivity subsystems if requested
    # ------------------------------------------------------------------
    if args.internet_access or args.websocket_feed or args.news_scraping:
        websocket_source = "binance" if args.websocket_feed else None
        api_source = args.api_source if args.internet_access else None
        connectivity_components = _initialize_connectivity(
            api_source=api_source,
            websocket_feed=websocket_source,
            news_scraping=args.news_scraping,
            cache_dir=args.cache_dir,
            api_keys_file=args.api_keys_file,
        )
        logger.info(
            "Connectivity module integration complete: {} components",
            len(connectivity_components),
        )

    # ------------------------------------------------------------------
    # Optional: instantiate all imported module systems
    # ------------------------------------------------------------------
    if args.integrate_all_modules:
        logger.info("Auto-integrating all available imported module systems")
        auto_integrated_modules = initialize_all_imported_modules(
            config=PROFITABILITY_CONFIG,
            existing_systems=core_systems,
        )

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
            if MT5Interface is None:
                raise ImportError("MT5Interface not available")
                
            with MT5Interface() as mt5i:
                # MLStrategyEngine accepts: use_price_prediction, use_pattern_recognition, use_sentiment
                if args.use_ml and MLStrategyEngine:
                    strategy_engine = MLStrategyEngine(
                        mt5i,
                        symbol=symbol,
                        use_price_prediction=True,
                        use_pattern_recognition=True,
                        use_sentiment=args.sentiment_analysis
                    )
                elif StrategyEngine:
                    strategy_engine = StrategyEngine(mt5i, symbol=symbol)
                else:
                    raise ImportError("No strategy engine available")
                
                if RiskManager is None:
                    raise ImportError("RiskManager not available")
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
    
    try:
        df = None
        if MT5Interface is None:
            raise ImportError("MT5Interface not available")
            
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
                        
                        # --- PROFITABILITY GATE: Only trade if profitable ---
                        # Filter signals through profitability requirements
                        signal_confidence = 0.0
                        best_signal = None
                        
                        if isinstance(signals, dict):
                            signal_confidence = signals.get('confidence', signals.get('strength', 0.5))
                            best_signal = signals
                        elif isinstance(signals, list) and signals:
                            # Handle Signal dataclass objects (have .confidence attribute)
                            confidences = []
                            for s in signals:
                                if hasattr(s, 'confidence'):
                                    confidences.append((s.confidence / 100.0 if s.confidence > 1 else s.confidence, s))
                                elif isinstance(s, dict):
                                    conf = safe_get(s, 'confidence', safe_get(s, 'strength', 0.5))
                                    confidences.append((conf, s))
                                else:
                                    confidences.append((0.5, s))
                            if confidences:
                                signal_confidence, best_signal = max(confidences, key=lambda x: x[0])
                        
                        min_confidence = PROFITABILITY_CONFIG['min_confidence']
                        if signal_confidence < min_confidence:
                            logger.info(f"Signal confidence {signal_confidence:.2f} below threshold {min_confidence} - skipping (signals: {len(signals) if isinstance(signals, list) else 1})")
                            await asyncio.sleep(5)
                            continue
                        
                        logger.info(f"Signal passed confidence gate: {signal_confidence:.2f} >= {min_confidence}")
                        
                        # --- INTEGRATED SYSTEMS: Signal Enhancement ---
                        if integrated_systems and integrated_systems.initialized:
                            try:
                                # Enhance signal through AI systems
                                enhanced_signal = await integrated_systems.enhance_signal(
                                    best_signal if isinstance(best_signal, dict) else {'confidence': signal_confidence},
                                    df
                                )
                                if enhanced_signal:
                                    logger.info(f"Signal enhanced by integrated systems")
                                    if isinstance(best_signal, dict):
                                        best_signal.update(enhanced_signal)
                                
                                # Get market intelligence
                                market_intel = await integrated_systems.get_market_intelligence(symbol, df)
                                if market_intel:
                                    logger.debug(f"Market intelligence: {list(market_intel.keys())}")
                            except Exception as e:
                                logger.debug(f"Signal enhancement skipped: {e}")
                        
                        # --- Position sizing and execution ---
                        position = 0
                        stop_loss_pips = 20  # Default
                        
                        # Extract stop_loss_pips from best_signal
                        if best_signal is not None:
                            if hasattr(best_signal, 'stop_loss_pips'):
                                stop_loss_pips = best_signal.stop_loss_pips
                            elif isinstance(best_signal, dict):
                                stop_loss_pips = safe_get(best_signal, 'stop_loss_pips', 20)
                        
                        try:
                            pos = trader['risk'].calculate_position_size(symbol=symbol, stop_loss_pips=stop_loss_pips)
                            if hasattr(pos, 'lot') and pos.lot > 0:
                                position = pos
                                logger.info(f"Position size calculated: {pos.lot} lots")
                            elif isinstance(pos, (int, float)) and pos > 0:
                                position = pos
                                logger.info(f"Position size calculated: {pos} lots")
                            else:
                                # Fallback: use minimum lot size for paper trading
                                logger.warning(f"Position size returned {pos}, using fallback 0.01 lots")
                                position = 0.01
                        except Exception as e:
                            logger.warning(f"Position sizing error: {e}, using fallback 0.01 lots")
                            position = 0.01
                        
                        trade_executed = False
                        trade_direction = 0
                        trade_size = 0
                        MAX_LOT_CAP = 10.0  # Sensible cap for paper trading
                        
                        # Determine direction from best_signal
                        sig_action = 'buy'  # Default
                        if best_signal is not None:
                            if hasattr(best_signal, 'direction'):
                                sig_action = best_signal.direction
                            elif isinstance(best_signal, dict):
                                sig_action = best_signal.get('action', best_signal.get('direction', 'buy'))
                        
                        _sig_dir = -1 if str(sig_action).lower() in ('sell', 'short', '-1') else 1
                        logger.info(f"Trade direction: {'SELL' if _sig_dir < 0 else 'BUY'}")
                        
                        # Execute the trade
                        trade_direction = _sig_dir
                        if hasattr(position, 'lot') and position.lot > 0:
                            trade_size = min(abs(position.lot), MAX_LOT_CAP)
                        elif isinstance(position, (int, float)) and position > 0:
                            trade_size = min(abs(position), MAX_LOT_CAP)
                        else:
                            trade_size = 0.01  # Minimum fallback
                        
                        # --- INTEGRATED SYSTEMS: Safety Validation (VETO POWER) ---
                        trade_allowed = True
                        if integrated_systems and integrated_systems.initialized:
                            try:
                                is_valid, reason, adjustments = integrated_systems.validate_trade(
                                    symbol=symbol,
                                    direction=trade_direction,
                                    size=trade_size,
                                    signal_data=best_signal if isinstance(best_signal, dict) else {}
                                )
                                if not is_valid:
                                    logger.warning(f"Trade BLOCKED by safety systems: {reason}")
                                    trade_allowed = False
                                else:
                                    logger.info(f"Trade APPROVED by safety systems")
                                    # Apply any adjustments from risk system
                                    if 'size' in adjustments:
                                        trade_size = adjustments['size']
                                        logger.info(f"Position size adjusted to: {trade_size}")
                            except Exception as e:
                                logger.warning(f"Safety validation error (allowing trade): {e}")
                        
                        if not trade_allowed:
                            logger.info("Trade skipped due to safety veto")
                            await asyncio.sleep(5)
                            continue
                        
                        logger.info(f"EXECUTING TRADE: {symbol} {'BUY' if trade_direction > 0 else 'SELL'} {trade_size} lots")
                        await trader['executor'].execute_trade(
                            symbol=symbol,
                            direction=trade_direction,
                            size=trade_size
                        )
                        trade_executed = True
                        logger.success(f"Trade executed successfully: {symbol} {'BUY' if trade_direction > 0 else 'SELL'} {trade_size} lots")
                        
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
        # Stop background services if they were started.
        if background_manager is not None:
            stop_all = getattr(background_manager, "stop_all", None)
            if callable(stop_all):
                try:
                    result = stop_all()
                    if asyncio.iscoroutine(result):
                        await result
                    logger.info("Background services stopped")
                except Exception as e:
                    logger.warning(f"Error stopping background services: {e}")

        # Shutdown MASTER INTEGRATION ENGINE
        if _master_engine is not None:
            try:
                await _master_engine.stop_all()
                logger.info("MasterIntegrationEngine shutdown complete")
            except Exception as _eng_stop_err:
                logger.warning(f"Engine shutdown error: {_eng_stop_err}")

        # Shutdown INTEGRATED SYSTEMS (unified orchestration)
        if integrated_systems is not None:
            try:
                await integrated_systems.shutdown()
                logger.info("Integrated systems shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down integrated systems: {e}")
        
        # Shutdown auto-integrated modules and core systems cleanly.
        if auto_integrated_modules:
            await shutdown_integrated_modules(
                auto_integrated_modules,
                label="auto-integrated module",
            )
        if core_systems:
            await shutdown_integrated_modules(core_systems, label="core system")

        # Cleanup - mt5i handled by context manager
        logger.info("Trading bot shutdown complete")
    
    logger.success("Run finished successfully â˜‘")


if __name__ == "__main__":
    asyncio.run(main())

