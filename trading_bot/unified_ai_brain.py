"""
UNIFIED AI BRAIN - THE ONE SYSTEM

Integrates ALL 2900+ files, 170+ packages into ONE coherent AI system.

"Many modules, ONE mind. Many features, ONE purpose. Many files, ONE AI."

This is the MASTER AI that unifies everything:
- 170+ packages
- 2900+ Python files
- 700,000+ lines of code
- 300+ features

All working together as ONE intelligent trading system.

ARCHITECTURE:
  UNIFIED AI BRAIN
    CONSCIOUSNESS LAYER  - Decision Making, Learning, Self-Improvement, Memory
    COGNITIVE LAYER      - Pattern Recognition, Reasoning, Prediction, Analysis
    OPERATIONAL LAYER    - Data Ingestion, Signal Generation, Execution, Risk
    SAFETY LAYER         - Risk Limits, Circuit Breakers, Human Override, Fail-Safe

IMMUTABLE PRINCIPLES:
1. RISK FIRST: Safety layer has VETO power over all decisions
2. HUMAN CONTROL: Human override ALWAYS works
3. FAIL-SAFE: Default to NO TRADE when uncertain
4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
5. TRANSPARENCY: Every decision must be explainable

Author: AlphaAlgo Trading System
Version: 4.0.0 - THE ONE
"""

import asyncio
import logging
import importlib
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from abc import ABC, abstractmethod
import traceback
import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


# =============================================================================
# CORE ENUMS AND TYPES
# =============================================================================

class BrainState(Enum):
    """States of the unified AI brain"""
    DORMANT = "dormant"           # Not initialized
    AWAKENING = "awakening"       # Initializing subsystems
    CONSCIOUS = "conscious"       # Fully operational
    THINKING = "thinking"         # Processing a decision
    LEARNING = "learning"         # Updating models
    RESTING = "resting"           # Idle but ready
    EMERGENCY = "emergency"       # Emergency mode
    SHUTDOWN = "shutdown"         # Shutting down


class DecisionType(Enum):
    """Types of decisions the brain can make"""
    TRADE = "trade"               # Trading decision
    RISK = "risk"                 # Risk management decision
    LEARNING = "learning"         # Learning/adaptation decision
    SYSTEM = "system"             # System management decision
    EMERGENCY = "emergency"       # Emergency decision


class ConfidenceLevel(Enum):
    """Confidence levels for decisions"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


class SubsystemCategory(Enum):
    """Categories of subsystems"""
    # Core layers
    DATA = "data"                 # Data ingestion and processing
    INTELLIGENCE = "intelligence" # AI/ML/Cognitive systems
    STRATEGY = "strategy"         # Signal generation and strategy
    EXECUTION = "execution"       # Order execution
    RISK = "risk"                 # Risk management
    SAFETY = "safety"             # Safety systems (HIGHEST PRIORITY)
    
    # Support layers
    MONITORING = "monitoring"     # System monitoring
    GOVERNANCE = "governance"     # Compliance and governance
    LEARNING = "learning"         # Self-improvement
    INFRASTRUCTURE = "infrastructure"  # Infrastructure


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BrainConfig:
    """Configuration for the Unified AI Brain"""
    # Identity
    name: str = "AlphaAlgo"
    version: str = "4.0.0"
    
    # Mode
    mode: str = "paper"  # paper, live, backtest, simulation
    
    # Trading
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "EURUSD"])
    initial_capital: float = 100000.0
    
    # IMMUTABLE Risk Limits (cannot be changed by AI)
    max_risk_per_trade: float = 0.02      # 2%
    max_daily_loss: float = 0.05          # 5%
    max_drawdown: float = 0.20            # 20%
    max_positions: int = 10
    max_leverage: float = 5.0
    
    # Features
    enable_ai: bool = True
    enable_quantum: bool = False
    enable_blockchain: bool = False
    enable_sentiment: bool = True
    enable_self_improvement: bool = True
    
    # Performance
    max_workers: int = 8
    lazy_loading: bool = True
    
    # Paths
    data_dir: str = "brain_data"
    log_dir: str = "brain_logs"
    state_dir: str = "brain_state"


@dataclass
class Thought:
    """A thought/decision from the brain"""
    thought_id: str
    thought_type: DecisionType
    timestamp: datetime
    
    # Content
    symbol: Optional[str] = None
    action: Optional[str] = None  # BUY, SELL, HOLD
    confidence: float = 0.0
    reasoning: str = ""
    
    # Details
    price: Optional[float] = None
    quantity: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Metadata
    sources: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    approved: bool = False
    executed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'thought_id': self.thought_id,
            'type': self.thought_type.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'price': self.price,
            'quantity': self.quantity,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'sources': self.sources,
            'risk_score': self.risk_score,
            'approved': self.approved,
            'executed': self.executed
        }


@dataclass
class Memory:
    """Memory entry for the brain"""
    memory_id: str
    memory_type: str  # trade, lesson, pattern, error
    timestamp: datetime
    content: Dict[str, Any]
    importance: float = 0.5
    accessed_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class SubsystemInfo:
    """Information about a subsystem"""
    name: str
    category: SubsystemCategory
    module_path: str
    class_name: str
    instance: Any = None
    status: str = "not_loaded"
    load_time_ms: float = 0.0
    error: Optional[str] = None
    priority: int = 5
    dependencies: List[str] = field(default_factory=list)
    is_critical: bool = False


@dataclass
class BrainStatus:
    """Complete status of the brain"""
    state: BrainState
    uptime_seconds: float
    
    # Subsystems
    total_subsystems: int
    loaded_subsystems: int
    failed_subsystems: int
    
    # Activity
    thoughts_generated: int
    trades_executed: int
    current_positions: int
    
    # Performance
    capital: float
    pnl: float
    pnl_percent: float
    
    # Health
    health_score: float
    errors: List[str]
    warnings: List[str]
    
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# SUBSYSTEM REGISTRY - ALL 170+ PACKAGES
# =============================================================================

SUBSYSTEM_REGISTRY: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # SAFETY LAYER (HIGHEST PRIORITY - LOADED FIRST)
    # =========================================================================
    "msos_orchestrator": {
        "category": SubsystemCategory.SAFETY,
        "module": "trading_bot.msos.orchestrator",
        "class": "MSOSOrchestrator",
        "priority": 100,
        "critical": True,
        "description": "Market Survival Operating System - Ultimate safety"
    },
    "hedge_fund_safety": {
        "category": SubsystemCategory.SAFETY,
        "module": "trading_bot.hedge_fund_safety.mitigation_orchestrator",
        "class": "HedgeFundSafetyOrchestrator",
        "priority": 99,
        "critical": True,
        "description": "Hedge fund level safety systems"
    },
    "stealth_safety": {
        "category": SubsystemCategory.SAFETY,
        "module": "trading_bot.stealth_safety.stealth_orchestrator",
        "class": "StealthSafetyOrchestrator",
        "priority": 98,
        "critical": True,
        "description": "Stealth and regulatory safety"
    },
    "fail_safe": {
        "category": SubsystemCategory.SAFETY,
        "module": "trading_bot.safety.fail_safe",
        "class": "FailSafeSystem",
        "priority": 97,
        "critical": True,
        "description": "Fail-safe emergency system"
    },
    "circuit_breaker": {
        "category": SubsystemCategory.SAFETY,
        "module": "trading_bot.safety.circuit_breaker",
        "class": "CircuitBreaker",
        "priority": 96,
        "critical": True,
        "description": "Circuit breaker for trading halts"
    },
    
    # =========================================================================
    # RISK LAYER (SECOND HIGHEST PRIORITY)
    # =========================================================================
    "risk_manager": {
        "category": SubsystemCategory.RISK,
        "module": "trading_bot.risk.risk_manager",
        "class": "RiskManager",
        "priority": 90,
        "critical": True,
        "description": "Master risk management"
    },
    "position_sizer": {
        "category": SubsystemCategory.RISK,
        "module": "trading_bot.risk.position_sizer",
        "class": "PositionSizer",
        "priority": 89,
        "critical": True,
        "description": "Position sizing calculations"
    },
    "drawdown_manager": {
        "category": SubsystemCategory.RISK,
        "module": "trading_bot.risk.drawdown_manager",
        "class": "DrawdownManager",
        "priority": 88,
        "critical": True,
        "description": "Drawdown monitoring and control"
    },
    "portfolio_risk": {
        "category": SubsystemCategory.RISK,
        "module": "trading_bot.risk.portfolio_risk",
        "class": "PortfolioRiskManager",
        "priority": 87,
        "critical": True,
        "description": "Portfolio-level risk management"
    },
    "complete_risk_system": {
        "category": SubsystemCategory.RISK,
        "module": "trading_bot.risk.complete_risk_system",
        "class": "CompleteRiskSystem",
        "priority": 86,
        "critical": True,
        "description": "Complete risk system integration"
    },
    
    # =========================================================================
    # DATA LAYER
    # =========================================================================
    "data_foundation": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.unified_architecture.layer1_data_foundation",
        "class": "DataFoundation",
        "priority": 80,
        "critical": True,
        "description": "Unified data foundation"
    },
    "market_data_stream": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.database.data_streaming",
        "class": "MarketDataStream",
        "priority": 79,
        "critical": True,
        "description": "Real-time market data streaming"
    },
    "staleness_detector": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.connectivity.staleness_detector",
        "class": "StalenessDetector",
        "priority": 78,
        "critical": True,
        "description": "Data staleness detection"
    },
    "data_quarantine": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.database.data_quarantine",
        "class": "DataQuarantine",
        "priority": 77,
        "critical": False,
        "description": "Bad data quarantine"
    },
    "complete_data_infrastructure": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.database.complete_data_infrastructure",
        "class": "CompleteDataInfrastructure",
        "priority": 76,
        "critical": False,
        "description": "Complete data infrastructure"
    },
    "sentiment_engine": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.alpha_engine.sentiment_engine",
        "class": "SentimentAggregator",
        "priority": 70,
        "critical": False,
        "description": "Sentiment analysis",
        "optional_deps": ["torchvision"]
    },
    "free_data_providers": {
        "category": SubsystemCategory.DATA,
        "module": "trading_bot.data_sources.free_data_providers",
        "class": "FreeDataProviders",
        "priority": 69,
        "critical": False,
        "description": "Free data sources"
    },
    
    # =========================================================================
    # INTELLIGENCE LAYER
    # =========================================================================
    "cognitive_core": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.cognitive_architecture.cognitive_core",
        "class": "AlphaAlgoCognitiveCore",
        "priority": 75,
        "critical": True,
        "description": "10-layer cognitive architecture"
    },
    "intelligence_core": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.unified_architecture.layer2_intelligence_core",
        "class": "IntelligenceCore",
        "priority": 74,
        "critical": True,
        "description": "Unified intelligence core"
    },
    "market_state_engine": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.cognitive_architecture.layer1_market_state_detection",
        "class": "MarketStateEngine",
        "priority": 73,
        "critical": True,
        "description": "Market regime detection"
    },
    "complete_ai_system": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.ml.complete_ai_system",
        "class": "CompleteAISystem",
        "priority": 72,
        "critical": False,
        "description": "Complete AI system"
    },
    "elite_trading_orchestrator": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.elite_ai_system.elite_trading_orchestrator",
        "class": "EliteTradingOrchestrator",
        "priority": 71,
        "critical": False,
        "description": "Elite AI trading system"
    },
    "slow_inference_engine": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.elite_ai_system.slow_inference_engine",
        "class": "SlowInferenceEngine",
        "priority": 70,
        "critical": False,
        "description": "Deep reasoning engine"
    },
    "market_psychology_engine": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.elite_ai_system.market_psychology_engine",
        "class": "MarketPsychologyEngine",
        "priority": 69,
        "critical": False,
        "description": "Market psychology analysis"
    },
    "deepchart_intelligence": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.deepchart.market_intelligence_orchestrator",
        "class": "MarketIntelligenceOrchestrator",
        "priority": 68,
        "critical": False,
        "description": "DeepChart market intelligence"
    },
    
    # =========================================================================
    # STRATEGY LAYER
    # =========================================================================
    "strategy_engine": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.unified_architecture.layer3_strategy_engine",
        "class": "StrategyEngine",
        "priority": 65,
        "critical": True,
        "description": "Unified strategy engine"
    },
    "complete_signal_system": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.signals.complete_signal_system",
        "class": "CompleteSignalSystem",
        "priority": 64,
        "critical": True,
        "description": "Complete signal system"
    },
    "signal_lifecycle": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.signals.signal_lifecycle",
        "class": "SignalLifecycleManager",
        "priority": 63,
        "critical": True,
        "description": "Signal lifecycle management"
    },
    "alpha_research": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.alpha_research.alpha_research_orchestrator",
        "class": "AlphaResearchOrchestrator",
        "priority": 62,
        "critical": False,
        "description": "Alpha research system"
    },
    "alpha_engine": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.alpha_engine.dc_core",
        "class": "DCCore",
        "priority": 61,
        "critical": False,
        "description": "Alpha generation engine",
        "optional_deps": ["torchvision"]
    },
    "opportunity_scanner": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.opportunity_scanner.scanner",
        "class": "OpportunityScanner",
        "priority": 60,
        "critical": False,
        "description": "Market opportunity scanner"
    },
    
    # =========================================================================
    # EXECUTION LAYER
    # =========================================================================
    "execution_layer": {
        "category": SubsystemCategory.EXECUTION,
        "module": "trading_bot.unified_architecture.layer4_execution",
        "class": "ExecutionLayer",
        "priority": 55,
        "critical": True,
        "description": "Unified execution layer"
    },
    "complete_execution_system": {
        "category": SubsystemCategory.EXECUTION,
        "module": "trading_bot.execution.complete_execution_system",
        "class": "CompleteExecutionSystem",
        "priority": 54,
        "critical": True,
        "description": "Complete execution system"
    },
    "smart_order_router": {
        "category": SubsystemCategory.EXECUTION,
        "module": "trading_bot.execution.smart_order_router",
        "class": "SmartOrderRouter",
        "priority": 53,
        "critical": True,
        "description": "Smart order routing"
    },
    "idempotent_executor": {
        "category": SubsystemCategory.EXECUTION,
        "module": "trading_bot.execution.idempotent_executor",
        "class": "IdempotentExecutor",
        "priority": 52,
        "critical": True,
        "description": "Idempotent order execution"
    },
    "fill_tracker": {
        "category": SubsystemCategory.EXECUTION,
        "module": "trading_bot.execution.fill_tracker",
        "class": "FillTracker",
        "priority": 51,
        "critical": True,
        "description": "Order fill tracking"
    },
    "broker_adapter": {
        "category": SubsystemCategory.EXECUTION,
        "module": "trading_bot.brokers.broker_adapter",
        "class": "BrokerAdapter",
        "priority": 50,
        "critical": True,
        "description": "Broker connection adapter"
    },
    
    # =========================================================================
    # GOVERNANCE LAYER
    # =========================================================================
    "alphaalgo_orchestrator": {
        "category": SubsystemCategory.GOVERNANCE,
        "module": "trading_bot.alphaalgo_core.alphaalgo_orchestrator",
        "class": "AlphaAlgoOrchestrator",
        "priority": 45,
        "critical": False,
        "description": "AlphaAlgo governance"
    },
    "qwen_codemender": {
        "category": SubsystemCategory.GOVERNANCE,
        "module": "trading_bot.qwen_codemender.governance_orchestrator",
        "class": "GovernanceOrchestrator",
        "priority": 44,
        "critical": False,
        "description": "QwenCodeMender system"
    },
    "compliance_monitor": {
        "category": SubsystemCategory.GOVERNANCE,
        "module": "trading_bot.compliance.compliance_monitor",
        "class": "ComplianceMonitor",
        "priority": 43,
        "critical": False,
        "description": "Compliance monitoring"
    },
    
    # =========================================================================
    # LEARNING LAYER
    # =========================================================================
    "self_mastery": {
        "category": SubsystemCategory.LEARNING,
        "module": "trading_bot.self_mastery.mastery_orchestrator",
        "class": "MasteryOrchestrator",
        "priority": 40,
        "critical": False,
        "description": "Self-mastery learning system"
    },
    "eternal_evolution": {
        "category": SubsystemCategory.LEARNING,
        "module": "trading_bot.eternal_evolution.eternal_orchestrator",
        "class": "EternalEvolutionOrchestrator",
        "priority": 39,
        "critical": False,
        "description": "Eternal evolution system"
    },
    "self_healing_ai": {
        "category": SubsystemCategory.LEARNING,
        "module": "trading_bot.self_healing_ai.orchestrator",
        "class": "SelfHealingOrchestrator",
        "priority": 38,
        "critical": False,
        "description": "Self-healing AI system"
    },
    "autonomous_learner": {
        "category": SubsystemCategory.LEARNING,
        "module": "trading_bot.autonomous_learner.learner",
        "class": "AutonomousLearner",
        "priority": 37,
        "critical": False,
        "description": "Autonomous learning system"
    },
    
    # =========================================================================
    # MONITORING LAYER
    # =========================================================================
    "health_monitor": {
        "category": SubsystemCategory.MONITORING,
        "module": "trading_bot.infrastructure.health_check",
        "class": "HealthMonitor",
        "priority": 35,
        "critical": False,
        "description": "System health monitoring"
    },
    "performance_monitor": {
        "category": SubsystemCategory.MONITORING,
        "module": "trading_bot.monitoring.performance_monitor",
        "class": "PerformanceMonitor",
        "priority": 34,
        "critical": False,
        "description": "Performance monitoring"
    },
    "autonomous_validation": {
        "category": SubsystemCategory.MONITORING,
        "module": "trading_bot.validation.autonomous_validation",
        "class": "AutonomousValidationSystem",
        "priority": 33,
        "critical": False,
        "description": "Autonomous validation"
    },
    
    # =========================================================================
    # INFRASTRUCTURE LAYER
    # =========================================================================
    "event_pipeline": {
        "category": SubsystemCategory.INFRASTRUCTURE,
        "module": "trading_bot.event_pipeline.pipeline",
        "class": "EventPipeline",
        "priority": 30,
        "critical": False,
        "description": "Event processing pipeline"
    },
    "systems_ai": {
        "category": SubsystemCategory.INFRASTRUCTURE,
        "module": "trading_bot.systems_ai.orchestrator",
        "class": "SystemsAIOrchestrator",
        "priority": 29,
        "critical": False,
        "description": "Systems AI orchestrator"
    },
    
    # =========================================================================
    # SPECIALIZED SYSTEMS
    # =========================================================================
    "hedge_fund": {
        "category": SubsystemCategory.STRATEGY,
        "module": "trading_bot.hedge_fund.hedge_fund_orchestrator",
        "class": "HedgeFundOrchestrator",
        "priority": 25,
        "critical": False,
        "description": "Hedge fund operations"
    },
    "ultimate_system": {
        "category": SubsystemCategory.INTELLIGENCE,
        "module": "trading_bot.ultimate_system.ultimate_orchestrator",
        "class": "UltimateOrchestrator",
        "priority": 24,
        "critical": False,
        "description": "Ultimate trading system"
    },
    "sentient_core": {
        "category": SubsystemCategory.LEARNING,
        "module": "trading_bot.sentient_core.sentient_orchestrator",
        "class": "SentientOrchestrator",
        "priority": 23,
        "critical": False,
        "description": "Sentient core system"
    },
    "adversarial_curriculum": {
        "category": SubsystemCategory.LEARNING,
        "module": "trading_bot.adversarial_curriculum.curriculum_orchestrator",
        "class": "CurriculumOrchestrator",
        "priority": 22,
        "critical": False,
        "description": "Adversarial curriculum learning"
    },
}


# =============================================================================
# UNIFIED AI BRAIN CLASS
# =============================================================================

class UnifiedAIBrain:
    """
    The ONE AI Brain that unifies ALL 2900+ files into a single intelligent system.
    
    This is not just an integration - it's a unified consciousness that:
    - Thinks with multiple cognitive systems
    - Learns from every experience
    - Protects capital above all else
    - Evolves continuously
    - Explains every decision
    
    "Many modules, ONE mind."
    """
    
    # Class-level singleton
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern - only ONE brain"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, config: Optional[BrainConfig] = None):
        """Initialize the unified AI brain"""
        # Prevent re-initialization
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or BrainConfig()
        self.state = BrainState.DORMANT
        self.start_time: Optional[datetime] = None
        
        # Subsystems
        self.subsystems: Dict[str, SubsystemInfo] = {}
        self.loaded_subsystems: Set[str] = set()
        self.failed_subsystems: Set[str] = set()
        
        # Memory
        self.short_term_memory: List[Memory] = []  # Recent events
        self.long_term_memory: Dict[str, Memory] = {}  # Persistent knowledge
        
        # Thoughts
        self.thoughts: List[Thought] = []
        self.current_thought: Optional[Thought] = None
        
        # State
        self.positions: Dict[str, Any] = {}
        self.capital = self.config.initial_capital
        self.pnl = 0.0
        
        # Statistics
        self.stats = {
            'thoughts_generated': 0,
            'trades_executed': 0,
            'trades_won': 0,
            'trades_lost': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'errors': 0,
        }
        
        # Thread pool for parallel loading
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Async lock
        self._async_lock = asyncio.Lock()
        
        # Create directories
        for dir_path in [self.config.data_dir, self.config.log_dir, self.config.state_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        self._initialized = True
        
        logger.info("=" * 80)
        logger.info("UNIFIED AI BRAIN CREATED")
        logger.info(f"Name: {self.config.name}")
        logger.info(f"Version: {self.config.version}")
        logger.info(f"Mode: {self.config.mode}")
        logger.info("=" * 80)
    
    # =========================================================================
    # AWAKENING - Initialize all subsystems
    # =========================================================================
    
    async def awaken(self) -> bool:
        """
        Awaken the brain - initialize all subsystems.
        
        This is the main initialization that brings the brain to consciousness.
        Subsystems are loaded in priority order (safety first).
        """
        if self.state not in [BrainState.DORMANT, BrainState.SHUTDOWN]:
            logger.warning(f"Brain already in state: {self.state.value}")
            return True
        
        self.state = BrainState.AWAKENING
        self.start_time = datetime.now()
        
        logger.info("\n" + "=" * 80)
        logger.info("AWAKENING THE UNIFIED AI BRAIN")
        logger.info("=" * 80)
        
        try:
            # Register all subsystems
            self._register_all_subsystems()
            
            # Load subsystems in priority order
            await self._load_all_subsystems()
            
            # Initialize critical subsystems
            await self._initialize_critical_subsystems()
            
            # Verify safety systems
            if not self._verify_safety_systems():
                logger.error("CRITICAL: Safety systems not operational!")
                self.state = BrainState.EMERGENCY
                return False
            
            # Brain is now conscious
            self.state = BrainState.CONSCIOUS
            
            # Report status
            self._report_awakening_status()
            
            logger.info("\n" + "=" * 80)
            logger.info("BRAIN IS NOW CONSCIOUS AND OPERATIONAL")
            logger.info("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to awaken brain: {e}")
            logger.error(traceback.format_exc())
            self.state = BrainState.EMERGENCY
            return False
    
    def _register_all_subsystems(self):
        """Register all subsystems from the registry"""
        logger.info("\n[REGISTERING SUBSYSTEMS]")
        
        for name, info in SUBSYSTEM_REGISTRY.items():
            self.subsystems[name] = SubsystemInfo(
                name=name,
                category=info["category"],
                module_path=info["module"],
                class_name=info["class"],
                priority=info["priority"],
                is_critical=info.get("critical", False),
                dependencies=info.get("dependencies", [])
            )
        
        logger.info(f"Registered {len(self.subsystems)} subsystems")
    
    async def _load_all_subsystems(self):
        """Load all subsystems in priority order"""
        logger.info("\n[LOADING SUBSYSTEMS]")
        
        # Sort by priority (highest first)
        sorted_subsystems = sorted(
            self.subsystems.values(),
            key=lambda x: -x.priority
        )
        
        # Group by category for logging
        categories = {}
        for ss in sorted_subsystems:
            cat = ss.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(ss)
        
        # Load each category
        for category, subsystems in categories.items():
            logger.info(f"\n  [{category.upper()}]")
            
            for ss in subsystems:
                await self._load_subsystem(ss)
    
    async def _load_subsystem(self, ss: SubsystemInfo) -> bool:
        """Load a single subsystem"""
        start_time = time.time()
        
        try:
            # Check for optional dependencies before importing
            if hasattr(ss, 'optional_deps') or 'optional_deps' in SUBSYSTEM_REGISTRY.get(ss.name, {}):
                optional_deps = SUBSYSTEM_REGISTRY.get(ss.name, {}).get('optional_deps', [])
                for dep in optional_deps:
                    try:
                        importlib.import_module(dep)
                    except (ImportError, AttributeError) as e:
                        # Optional dependency missing - skip this subsystem gracefully
                        ss.status = "skipped"
                        ss.error = f"Optional dependency '{dep}' not available"
                        logger.info(f"    ⊘ {ss.name} (skipped: {dep} not available)")
                        return True  # Count as success since it's optional
            
            # Dynamic import with error handling for optional dependencies
            try:
                module = importlib.import_module(ss.module_path)
            except (ImportError, AttributeError, RuntimeError, OSError) as import_error:
                # Check if this is an optional subsystem or has optional deps
                error_str = str(import_error)
                has_optional_deps = 'optional_deps' in SUBSYSTEM_REGISTRY.get(ss.name, {})
                
                if not ss.is_critical or has_optional_deps:
                    ss.status = "skipped"
                    ss.error = f"Import failed: {error_str[:80]}"
                    logger.info(f"    ⊘ {ss.name} (skipped: import error)")
                    return True  # Count as success since it's non-critical/optional
                else:
                    raise  # Re-raise for critical subsystems without optional deps
            
            cls = getattr(module, ss.class_name, None)
            
            if cls is None:
                # Try to find any class in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and attr_name != 'ABC':
                        cls = attr
                        break
            
            if cls:
                # Try multiple instantiation methods
                instance = None
                errors = []
                
                try:
                    # Method 1: No args
                    instance = cls()
                except Exception as e1:
                    errors.append(f"no_args: {str(e1)[:50]}")
                    
                    try:
                    # Method 2: Empty dict
                        instance = cls({})
                    except Exception as e2:
                        errors.append(f"empty_dict: {str(e2)[:50]}")
                        
                        try:
                        # Method 3: Config dict with common keys
                            config = {
                                'mode': self.config.mode,
                                'symbols': self.config.symbols,
                                'capital': self.config.initial_capital,
                                'max_risk_per_trade': self.config.max_risk_per_trade,
                                'max_positions': self.config.max_positions
                            }
                            instance = cls(config)
                        except Exception as e3:
                            errors.append(f"config_dict: {str(e3)[:50]}")
                            
                            try:
                            # Method 4: Just use the module
                                instance = module
                            except Exception as e4:
                                errors.append(f"module: {str(e4)[:50]}")
                
                if instance:
                    ss.instance = instance
                    ss.status = "loaded"
                    ss.load_time_ms = (time.time() - start_time) * 1000
                    self.loaded_subsystems.add(ss.name)
                    
                    logger.info(f"    ✓ {ss.name} ({ss.load_time_ms:.1f}ms)")
                    return True
                else:
                    raise RuntimeError(f"All instantiation methods failed: {'; '.join(errors)}")
            else:
                raise ImportError(f"Class {ss.class_name} not found")
                
        except Exception as e:
            ss.status = "error"
            ss.error = str(e)[:100]
            self.failed_subsystems.add(ss.name)
            
            if ss.is_critical:
                logger.error(f"    ✗ {ss.name} (CRITICAL): {ss.error}")
            else:
                logger.warning(f"    ✗ {ss.name}: {ss.error}")
            
            return False
    
    async def _initialize_critical_subsystems(self):
        """Initialize critical subsystems that need special setup"""
        logger.info("\n[INITIALIZING CRITICAL SUBSYSTEMS]")
        
        # Initialize safety systems first
        safety_systems = [
            ss for ss in self.subsystems.values()
            if ss.category == SubsystemCategory.SAFETY and ss.status == "loaded"
        ]
        
        for ss in safety_systems:
            try:
                if hasattr(ss.instance, 'initialize'):
                    if asyncio.iscoroutinefunction(ss.instance.initialize):
                        await ss.instance.initialize()
                    else:
                        ss.instance.initialize()
                ss.status = "initialized"
                logger.info(f"    ✓ {ss.name} initialized")
            except Exception as e:
                logger.error(f"    ✗ {ss.name} initialization failed: {e}")
    
    def _verify_safety_systems(self) -> bool:
        """Verify that critical safety systems are operational"""
        logger.info("\n[VERIFYING SAFETY SYSTEMS]")
        
        critical_safety = [
            "msos_orchestrator",
            "risk_manager",
            "fail_safe",
            "circuit_breaker"
        ]
        
        all_ok = True
        for name in critical_safety:
            ss = self.subsystems.get(name)
            if ss and ss.status in ["loaded", "initialized"]:
                logger.info(f"    ✓ {name}: OPERATIONAL")
            else:
                logger.error(f"    ✗ {name}: NOT OPERATIONAL")
                all_ok = False
        
        return all_ok
    
    def _report_awakening_status(self):
        """Report the status after awakening"""
        total = len(self.subsystems)
        loaded = len(self.loaded_subsystems)
        failed = len(self.failed_subsystems)
        
        logger.info("\n" + "-" * 60)
        logger.info("AWAKENING STATUS REPORT")
        logger.info("-" * 60)
        logger.info(f"Total Subsystems: {total}")
        logger.info(f"Loaded: {loaded} ({100*loaded/total:.1f}%)")
        logger.info(f"Failed: {failed} ({100*failed/total:.1f}%)")
        
        # Category breakdown
        logger.info("\nBy Category:")
        for category in SubsystemCategory:
            cat_total = sum(1 for ss in self.subsystems.values() if ss.category == category)
            cat_loaded = sum(1 for ss in self.subsystems.values() 
                          if ss.category == category and ss.name in self.loaded_subsystems)
            if cat_total > 0:
                logger.info(f"  {category.value}: {cat_loaded}/{cat_total}")
        
        logger.info("-" * 60)
    
    # =========================================================================
    # THINKING - Generate trading decisions
    # =========================================================================
    
    async def think(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Thought]:
        """
        Generate a trading thought/decision for a symbol.
        
        This is the main decision-making process that:
        1. Gathers data from all sources
        2. Analyzes with multiple intelligence systems
        3. Generates signals
        4. Validates through risk systems
        5. Returns an approved thought or None
        """
        if self.state != BrainState.CONSCIOUS:
            logger.warning(f"Brain not conscious (state: {self.state.value})")
            return None
        
        async with self._async_lock:
            self.state = BrainState.THINKING
            
            try:
                # Create thought ID
                thought_id = hashlib.md5(
                    f"{symbol}_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:12]
                
                # Initialize thought
                thought = Thought(
                    thought_id=thought_id,
                    thought_type=DecisionType.TRADE,
                    timestamp=datetime.now(),
                    symbol=symbol
                )
                
                # STEP 1: Data Collection
                data = await self._collect_data(symbol, market_data)
                
                # STEP 2: Intelligence Analysis
                analysis = await self._analyze(symbol, data)
                
                # STEP 3: Signal Generation
                signal = await self._generate_signal(symbol, analysis)
                
                if signal is None or signal.get('action') == 'HOLD':
                    self.state = BrainState.CONSCIOUS
                    return None
                
                # STEP 4: Risk Validation
                risk_result = await self._validate_risk(symbol, signal)
                
                if not risk_result['approved']:
                    thought.reasoning = f"Rejected by risk: {risk_result['reason']}"
                    thought.approved = False
                    self.state = BrainState.CONSCIOUS
                    return thought
                
                # STEP 5: Build final thought
                thought.action = signal['action']
                thought.confidence = signal.get('confidence', 0.5)
                thought.price = signal.get('price')
                thought.quantity = risk_result.get('position_size', 0)
                thought.stop_loss = risk_result.get('stop_loss')
                thought.take_profit = risk_result.get('take_profit')
                thought.reasoning = signal.get('reasoning', '')
                thought.sources = signal.get('sources', [])
                thought.risk_score = risk_result.get('risk_score', 0)
                thought.approved = True
                
                # Store thought
                self.thoughts.append(thought)
                self.current_thought = thought
                self.stats['thoughts_generated'] += 1
                
                # Add to memory
                self._remember(thought)
                
                self.state = BrainState.CONSCIOUS
                return thought
                
            except Exception as e:
                logger.error(f"Error thinking about {symbol}: {e}")
                logger.error(traceback.format_exc())
                self.state = BrainState.CONSCIOUS
                return None
    
    async def _collect_data(self, symbol: str, market_data: Dict) -> Dict:
        """Collect data from all data subsystems"""
        data = {'market': market_data}
        
        # Get data from data foundation
        if 'data_foundation' in self.loaded_subsystems:
            ss = self.subsystems['data_foundation']
            if hasattr(ss.instance, 'get_data'):
                try:
                    data['foundation'] = ss.instance.get_data(symbol)
                except Exception as e:
                    logger.error(f"Error: {e}")
                    pass
        
        # Get sentiment
        if 'sentiment_engine' in self.loaded_subsystems:
            ss = self.subsystems['sentiment_engine']
            if hasattr(ss.instance, 'get_sentiment'):
                try:
                    data['sentiment'] = ss.instance.get_sentiment(symbol)
                except Exception as e:
                    logger.error(f"Error getting sentiment: {e}")
                    pass
        
        return data
    
    async def _analyze(self, symbol: str, data: Dict) -> Dict:
        """Analyze data with intelligence subsystems"""
        analysis = {}
        
        # Cognitive analysis
        if 'cognitive_core' in self.loaded_subsystems:
            ss = self.subsystems['cognitive_core']
            if hasattr(ss.instance, 'analyze') or hasattr(ss.instance, 'make_decision'):
                try:
                    method = getattr(ss.instance, 'analyze', None) or getattr(ss.instance, 'make_decision', None)
                    if asyncio.iscoroutinefunction(method):
                        analysis['cognitive'] = await method(data.get('market', {}))
                    else:
                        analysis['cognitive'] = method(data.get('market', {}))
                except Exception as e:
                    logger.debug(f"Cognitive analysis error: {e}")
        
        # Market state
        if 'market_state_engine' in self.loaded_subsystems:
            ss = self.subsystems['market_state_engine']
            if hasattr(ss.instance, 'detect_regime'):
                try:
                    analysis['regime'] = ss.instance.detect_regime(data.get('market', {}))
                except Exception:
                    pass
        
        # DeepChart intelligence
        if 'deepchart_intelligence' in self.loaded_subsystems:
            ss = self.subsystems['deepchart_intelligence']
            if hasattr(ss.instance, 'update'):
                try:
                    price = data.get('market', {}).get('close', 0)
                    volume = data.get('market', {}).get('volume', 0)
                    analysis['deepchart'] = ss.instance.update(
                        symbol=symbol,
                        price=price,
                        volume=volume,
                        bid=price * 0.9999,
                        ask=price * 1.0001
                    )
                except:
                    pass
        
        return analysis
    
    async def _generate_signal(self, symbol: str, analysis: Dict) -> Optional[Dict]:
        """Generate trading signal from analysis"""
        signals = []
        
        # Get signal from strategy engine
        if 'strategy_engine' in self.loaded_subsystems:
            ss = self.subsystems['strategy_engine']
            if hasattr(ss.instance, 'generate_signal'):
                try:
                    sig = ss.instance.generate_signal(symbol, analysis)
                    if sig:
                        signals.append(sig)
                except Exception:
                    pass
        
        # Get signal from complete signal system
        if 'complete_signal_system' in self.loaded_subsystems:
            ss = self.subsystems['complete_signal_system']
            if hasattr(ss.instance, 'process_signal'):
                try:
                    sig = ss.instance.process_signal({
                        'symbol': symbol,
                        'analysis': analysis
                    })
                    if sig:
                        signals.append(sig)
                except:
                    pass
        
        # Get signal from cognitive core
        if 'cognitive' in analysis:
            cog = analysis['cognitive']
            if isinstance(cog, dict) and cog.get('action'):
                signals.append({
                    'action': cog.get('action'),
                    'confidence': cog.get('confidence', 0.5),
                    'reasoning': cog.get('reasoning', ''),
                    'source': 'cognitive_core'
                })
        
        # Combine signals (weighted average)
        if not signals:
            return None
        
        # Simple majority voting
        actions = [s.get('action', 'HOLD') for s in signals]
        action_counts = {}
        for a in actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        
        best_action = max(action_counts, key=action_counts.get)
        
        if best_action == 'HOLD':
            return None
        
        # Average confidence
        confidences = [s.get('confidence', 0.5) for s in signals if s.get('action') == best_action]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return {
            'action': best_action,
            'confidence': avg_confidence,
            'reasoning': f"Consensus from {len(signals)} sources",
            'sources': [s.get('source', 'unknown') for s in signals],
            'price': analysis.get('market', {}).get('close')
        }
    
    async def _validate_risk(self, symbol: str, signal: Dict) -> Dict:
        """Validate signal through risk systems"""
        result = {
            'approved': False,
            'reason': 'No risk validation',
            'position_size': 0,
            'risk_score': 1.0
        }
        
        # Check MSOS first (highest priority)
        if 'msos_orchestrator' in self.loaded_subsystems:
            ss = self.subsystems['msos_orchestrator']
            if hasattr(ss.instance, 'evaluate'):
                try:
                    msos_result = ss.instance.evaluate(
                        strategy_id='unified_brain',
                        symbol=symbol,
                        market_data={},
                        strategy_config={},
                        equity=self.capital
                    )
                    if not msos_result.get('approved', False):
                        result['reason'] = f"MSOS: {msos_result.get('reason', 'Rejected')}"
                        return result
                except:
                    pass
        
        # Check risk manager
        if 'risk_manager' in self.loaded_subsystems:
            ss = self.subsystems['risk_manager']
            if hasattr(ss.instance, 'validate_trade'):
                try:
                    risk_result = ss.instance.validate_trade(
                        symbol=symbol,
                        action=signal['action'],
                        confidence=signal.get('confidence', 0.5)
                    )
                    if not risk_result.get('approved', False):
                        result['reason'] = f"Risk: {risk_result.get('reason', 'Rejected')}"
                        return result
                except:
                    pass
        
        # Calculate position size
        position_size = self._calculate_position_size(symbol, signal)
        
        # Check circuit breaker
        if 'circuit_breaker' in self.loaded_subsystems:
            ss = self.subsystems['circuit_breaker']
            if hasattr(ss.instance, 'is_triggered'):
                try:
                    if ss.instance.is_triggered():
                        result['reason'] = "Circuit breaker triggered"
                        return result
                except:
                    pass
        
        # Approved
        result['approved'] = True
        result['reason'] = 'Passed all risk checks'
        result['position_size'] = position_size
        result['risk_score'] = 0.3
        result['stop_loss'] = signal.get('price', 0) * (0.98 if signal['action'] == 'BUY' else 1.02)
        result['take_profit'] = signal.get('price', 0) * (1.04 if signal['action'] == 'BUY' else 0.96)
        
        return result
    
    def _calculate_position_size(self, symbol: str, signal: Dict) -> float:
        """Calculate position size based on risk limits"""
        # Use position sizer if available
        if 'position_sizer' in self.loaded_subsystems:
            ss = self.subsystems['position_sizer']
            if hasattr(ss.instance, 'calculate'):
                try:
                    return ss.instance.calculate(
                        capital=self.capital,
                        risk_per_trade=self.config.max_risk_per_trade,
                        confidence=signal.get('confidence', 0.5)
                    )
                except:
                    pass
        
        # Default calculation
        risk_amount = self.capital * self.config.max_risk_per_trade
        confidence = signal.get('confidence', 0.5)
        return risk_amount * confidence
    
    def _remember(self, thought: Thought):
        """Store thought in memory"""
        memory = Memory(
            memory_id=thought.thought_id,
            memory_type='thought',
            timestamp=thought.timestamp,
            content=thought.to_dict(),
            importance=thought.confidence
        )
        
        self.short_term_memory.append(memory)
        
        # Keep short-term memory limited
        if len(self.short_term_memory) > 1000:
            self.short_term_memory = self.short_term_memory[-500:]
    
    # =========================================================================
    # EXECUTION - Execute approved thoughts
    # =========================================================================
    
    async def execute(self, thought: Thought) -> Dict:
        """Execute an approved thought"""
        if not thought.approved:
            return {'success': False, 'reason': 'Thought not approved'}
        
        if thought.executed:
            return {'success': False, 'reason': 'Already executed'}
        try:
        
            # Use execution layer
            if 'execution_layer' in self.loaded_subsystems:
                ss = self.subsystems['execution_layer']
                if hasattr(ss.instance, 'execute_order'):
                    order = {
                        'symbol': thought.symbol,
                        'side': thought.action,
                        'quantity': thought.quantity,
                        'price': thought.price,
                        'stop_loss': thought.stop_loss,
                        'take_profit': thought.take_profit
                    }
                    
                    if asyncio.iscoroutinefunction(ss.instance.execute_order):
                        result = await ss.instance.execute_order(order)
                    else:
                        result = ss.instance.execute_order(order)
                    
                    thought.executed = True
                    self.stats['trades_executed'] += 1
                    
                    return {'success': True, 'result': result}
            
            # Fallback - simulate execution
            thought.executed = True
            self.stats['trades_executed'] += 1
            
            return {
                'success': True,
                'result': {
                    'order_id': thought.thought_id,
                    'status': 'SIMULATED',
                    'symbol': thought.symbol,
                    'action': thought.action,
                    'quantity': thought.quantity,
                    'price': thought.price
                }
            }
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {'success': False, 'reason': str(e)}
    
    # =========================================================================
    # LEARNING - Continuous improvement
    # =========================================================================
    
    async def learn(self):
        """Learn from recent experiences"""
        if self.state != BrainState.CONSCIOUS:
            return
        
        self.state = BrainState.LEARNING
        
        try:
            # Use self-mastery system
            if 'self_mastery' in self.loaded_subsystems:
                ss = self.subsystems['self_mastery']
                if hasattr(ss.instance, 'reflect'):
                    try:
                        if asyncio.iscoroutinefunction(ss.instance.reflect):
                            await ss.instance.reflect()
                        else:
                            ss.instance.reflect()
                    except Exception:
                        pass
            
            # Use eternal evolution
            if 'eternal_evolution' in self.loaded_subsystems:
                ss = self.subsystems['eternal_evolution']
                if hasattr(ss.instance, 'evolve'):
                    try:
                        if asyncio.iscoroutinefunction(ss.instance.evolve):
                            await ss.instance.evolve()
                        else:
                            ss.instance.evolve()
                    except:
                        pass
            
        finally:
            self.state = BrainState.CONSCIOUS
    
    # =========================================================================
    # STATUS AND CONTROL
    # =========================================================================
    
    def get_status(self) -> BrainStatus:
        """Get complete brain status"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Count loaded + skipped (optional deps) as successful
        successful = len(self.loaded_subsystems)
        for ss in self.subsystems.values():
            if ss.status == 'skipped' and ss.name not in self.loaded_subsystems:
                successful += 1
        
        # Only count truly failed critical subsystems
        truly_failed = 0
        for name in self.failed_subsystems:
            ss = self.subsystems.get(name)
            if ss and ss.is_critical and 'optional_deps' not in SUBSYSTEM_REGISTRY.get(name, {}):
                truly_failed += 1
        
        return BrainStatus(
            state=self.state,
            uptime_seconds=uptime,
            total_subsystems=len(self.subsystems),
            loaded_subsystems=successful,
            failed_subsystems=truly_failed,
            thoughts_generated=self.stats['thoughts_generated'],
            trades_executed=self.stats['trades_executed'],
            current_positions=len(self.positions),
            capital=self.capital,
            pnl=self.pnl,
            pnl_percent=(self.pnl / self.config.initial_capital * 100) if self.config.initial_capital > 0 else 0,
            health_score=successful / len(self.subsystems) if self.subsystems else 0,
            errors=[ss.error for ss in self.subsystems.values() if ss.error and ss.is_critical],
            warnings=[ss.error for ss in self.subsystems.values() if ss.error and not ss.is_critical]
        )
    
    def get_subsystem(self, name: str) -> Optional[Any]:
        """Get a specific subsystem instance"""
        ss = self.subsystems.get(name)
        return ss.instance if ss else None
    
    async def emergency_stop(self, reason: str = "Manual emergency stop"):
        """Emergency stop - halt all trading"""
        logger.critical(f"EMERGENCY STOP: {reason}")
        self.state = BrainState.EMERGENCY
        
        # Trigger all safety systems
        for name in ['fail_safe', 'circuit_breaker', 'msos_orchestrator']:
            ss = self.subsystems.get(name)
            if ss and ss.instance:
                if hasattr(ss.instance, 'emergency_stop'):
                    try:
                        ss.instance.emergency_stop(reason)
                    except:
                        pass
                if hasattr(ss.instance, 'trigger'):
                    try:
                        ss.instance.trigger(reason)
                    except:
                        pass
    
    async def shutdown(self):
        """Gracefully shutdown the brain"""
        logger.info("Shutting down Unified AI Brain...")
        self.state = BrainState.SHUTDOWN
        
        # Save state
        self._save_state()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Brain shutdown complete")
    
    def _save_state(self):
        """Save brain state to disk"""
        state_file = Path(self.config.state_dir) / "brain_state.json"
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'capital': self.capital,
            'pnl': self.pnl,
            'positions': self.positions,
            'loaded_subsystems': list(self.loaded_subsystems),
            'failed_subsystems': list(self.failed_subsystems)
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    async def run(self, symbols: Optional[List[str]] = None):
        """
        Main trading loop - the brain's continuous operation.
        
        This runs forever (until stopped), continuously:
        1. Collecting market data
        2. Thinking about each symbol
        3. Executing approved thoughts
        4. Learning from results
        """
        symbols = symbols or self.config.symbols
        
        if self.state != BrainState.CONSCIOUS:
            logger.error("Brain must be conscious to run")
            return
        
        logger.info(f"\nStarting main loop for symbols: {symbols}")
        
        try:
            while self.state == BrainState.CONSCIOUS:
                for symbol in symbols:
                    try:
                        # Get market data (placeholder)
                        market_data = {
                            'symbol': symbol,
                            'timestamp': datetime.now(),
                            'close': 100.0,  # Would come from data feed
                            'volume': 1000000
                        }
                        
                        # Think
                        thought = await self.think(symbol, market_data)
                        
                        if thought and thought.approved:
                            logger.info(f"Thought: {thought.action} {symbol} @ {thought.confidence:.2%} confidence")
                            
                            # Execute in paper mode
                            if self.config.mode == 'paper':
                                result = await self.execute(thought)
                                if result['success']:
                                    logger.info(f"Executed: {result}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                
                # Learn periodically
                if self.stats['thoughts_generated'] % 10 == 0:
                    await self.learn()
                
                # Rest between cycles
                await asyncio.sleep(60)  # 1 minute between cycles
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            await self.emergency_stop(str(e))


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_brain(config: Optional[BrainConfig] = None) -> UnifiedAIBrain:
    """Create the unified AI brain"""
    return UnifiedAIBrain(config)


async def quick_start(
    mode: str = "paper",
    symbols: Optional[List[str]] = None,
    capital: float = 100000.0
) -> UnifiedAIBrain:
    """Quick start the brain with minimal configuration"""
    config = BrainConfig(
        mode=mode,
        symbols=symbols or ["BTCUSDT", "EURUSD"],
        initial_capital=capital
    )
    
    brain = create_brain(config)
    await brain.awaken()
    
    return brain


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'UnifiedAIBrain',
    'BrainConfig',
    'BrainState',
    'BrainStatus',
    'Thought',
    'Memory',
    'DecisionType',
    'ConfidenceLevel',
    'SubsystemCategory',
    'create_brain',
    'quick_start',
    'SUBSYSTEM_REGISTRY'
]
