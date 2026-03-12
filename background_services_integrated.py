#!/usr/bin/env python3
"""
AlphaAlgo Trading Bot - Unified Background Services
====================================================

This is the SINGLE background services manager that integrates ALL background
modules from the trading_bot package.

Services Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BACKGROUND SERVICES MANAGER                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: CRITICAL SERVICES (Always Running)                         │   │
│  │  • System Health Monitor    • Emergency Kill Switch                 │   │
│  │  • Risk Monitor             • Circuit Breaker Monitor               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: LEARNING SERVICES (Continuous Learning)                    │   │
│  │  • Market Student           • Eternal Evolution                     │   │
│  │  • Self-Diagnostic          • Knowledge Harvester                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 3: INTELLIGENCE SERVICES (Market Analysis)                    │   │
│  │  • Sentiment Monitor        • News Collector                        │   │
│  │  • Regime Detector          • Correlation Monitor                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 4: OPTIMIZATION SERVICES (Performance Tuning)                 │   │
│  │  • Strategy Optimizer       • Parameter Tuner                       │   │
│  │  • Performance Analyzer     • Backtest Runner                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 5: MAINTENANCE SERVICES (System Maintenance)                  │   │
│  │  • Data Cleanup             • Log Rotation                          │   │
│  │  • Model Retraining         • Database Maintenance                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

Usage:
    python background_services_integrated.py
    python background_services_integrated.py --tier 1,2,3
    python background_services_integrated.py --service market_student

Author: AlphaAlgo Team
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure directories exist
Path('logs').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/background_services.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BackgroundServices')


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class ServiceTier(Enum):
    """Service tier classification."""
    CRITICAL = 1      # Always running, highest priority
    LEARNING = 2      # Continuous learning services
    INTELLIGENCE = 3  # Market intelligence services
    OPTIMIZATION = 4  # Performance optimization
    MAINTENANCE = 5   # System maintenance


class ServiceStatus(Enum):
    """Service status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"


class ServicePriority(Enum):
    """Service priority for resource allocation."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class ServiceHealth:
    """Service health status."""
    healthy: bool
    last_check: datetime
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    restart_count: int = 0


@dataclass
class ServiceConfig:
    """Service configuration."""
    name: str
    tier: ServiceTier
    priority: ServicePriority = ServicePriority.NORMAL
    interval: float = 60.0  # seconds
    enabled: bool = True
    auto_restart: bool = True
    max_restarts: int = 3
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# BASE SERVICE CLASS
# =============================================================================

class BaseBackgroundService(ABC):
    """Base class for all background services."""
    
    SERVICE_NAME: str = "base_service"
    SERVICE_TIER: ServiceTier = ServiceTier.MAINTENANCE
    SERVICE_PRIORITY: ServicePriority = ServicePriority.NORMAL
    DEFAULT_INTERVAL: float = 60.0
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.status = ServiceStatus.STOPPED
        self.health = ServiceHealth(
            healthy=True,
            last_check=datetime.now(),
            message="Not started"
        )
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_run: Optional[datetime] = None
        self._error_count = 0
        self._restart_count = 0
        
        logger.debug(f"Service {self.SERVICE_NAME} initialized")
    
    @abstractmethod
    async def execute(self) -> None:
        """Execute the service's main task. Override in subclass."""
        pass
    
    async def start(self) -> None:
        """Start the service."""
        if self._running:
            logger.warning(f"Service {self.SERVICE_NAME} already running")
            return
        
        self._running = True
        self.status = ServiceStatus.STARTING
        logger.info(f"Starting service: {self.SERVICE_NAME}")
        
        try:
            await self.on_start()
            self.status = ServiceStatus.RUNNING
            self._task = asyncio.create_task(self._run_loop())
        except Exception as e:
            logger.error(f"Failed to start {self.SERVICE_NAME}: {e}")
            self.status = ServiceStatus.ERROR
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop the service."""
        if not self._running:
            return
        
        self.status = ServiceStatus.STOPPING
        self._running = False
        logger.info(f"Stopping service: {self.SERVICE_NAME}")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        await self.on_stop()
        self.status = ServiceStatus.STOPPED
    
    async def _run_loop(self) -> None:
        """Main service loop."""
        interval = self.config.get('interval', self.DEFAULT_INTERVAL)
        
        while self._running:
            try:
                self._last_run = datetime.now()
                await self.execute()
                self._error_count = 0
                self.health = ServiceHealth(
                    healthy=True,
                    last_check=datetime.now(),
                    message="OK",
                    error_count=self._error_count,
                    restart_count=self._restart_count
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._error_count += 1
                logger.error(f"Error in {self.SERVICE_NAME}: {e}")
                self.health = ServiceHealth(
                    healthy=False,
                    last_check=datetime.now(),
                    message=str(e),
                    error_count=self._error_count,
                    restart_count=self._restart_count
                )
                
                if self._error_count >= 3:
                    logger.error(f"Service {self.SERVICE_NAME} has too many errors, pausing")
                    self.status = ServiceStatus.ERROR
                    await asyncio.sleep(interval * 5)  # Extended pause
                    self._error_count = 0
            
            await asyncio.sleep(interval)
    
    async def on_start(self) -> None:
        """Called when service starts. Override for initialization."""
        pass
    
    async def on_stop(self) -> None:
        """Called when service stops. Override for cleanup."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'name': self.SERVICE_NAME,
            'tier': self.SERVICE_TIER.name,
            'status': self.status.value,
            'healthy': self.health.healthy,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'error_count': self._error_count,
            'restart_count': self._restart_count,
            'message': self.health.message
        }


# =============================================================================
# TIER 1: CRITICAL SERVICES
# =============================================================================

class SystemHealthMonitor(BaseBackgroundService):
    """Monitors overall system health."""
    
    SERVICE_NAME = "system_health_monitor"
    SERVICE_TIER = ServiceTier.CRITICAL
    SERVICE_PRIORITY = ServicePriority.CRITICAL
    DEFAULT_INTERVAL = 10.0
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.metrics = {}
    
    async def execute(self) -> None:
        """Check system health."""
        import psutil
        
        self.metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
            'timestamp': datetime.now().isoformat()
        }
        
        # Alert on high resource usage
        if self.metrics['cpu_percent'] > 90:
            logger.warning(f"High CPU usage: {self.metrics['cpu_percent']}%")
        if self.metrics['memory_percent'] > 90:
            logger.warning(f"High memory usage: {self.metrics['memory_percent']}%")
        
        logger.debug(f"System health: CPU={self.metrics['cpu_percent']}%, MEM={self.metrics['memory_percent']}%")


class RiskMonitorService(BaseBackgroundService):
    """Monitors risk levels in real-time."""
    
    SERVICE_NAME = "risk_monitor"
    SERVICE_TIER = ServiceTier.CRITICAL
    SERVICE_PRIORITY = ServicePriority.CRITICAL
    DEFAULT_INTERVAL = 5.0
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.risk_manager = None
        self.alerts = []
    
    async def on_start(self) -> None:
        """Initialize risk manager."""
        try:
            from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
            self.risk_manager = MasterRiskManager()
        except ImportError:
            logger.warning("Risk manager not available")
    
    async def execute(self) -> None:
        """Monitor risk levels."""
        if not self.risk_manager:
            return
        
        try:
            # Check drawdown
            if hasattr(self.risk_manager, 'current_drawdown'):
                drawdown = self.risk_manager.current_drawdown
                if drawdown > 0.1:  # 10%
                    self.alerts.append({
                        'type': 'drawdown',
                        'level': 'warning',
                        'value': drawdown,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.warning(f"Drawdown alert: {drawdown:.1%}")
                
                if drawdown > 0.2:  # 20%
                    logger.critical(f"CRITICAL DRAWDOWN: {drawdown:.1%}")
            
            # Check daily loss
            if hasattr(self.risk_manager, 'daily_loss'):
                daily_loss = self.risk_manager.daily_loss
                if daily_loss > 0.03:  # 3%
                    logger.warning(f"Daily loss alert: {daily_loss:.1%}")
                    
        except Exception as e:
            logger.error(f"Risk monitoring error: {e}")


class CircuitBreakerMonitor(BaseBackgroundService):
    """Monitors circuit breaker status."""
    
    SERVICE_NAME = "circuit_breaker_monitor"
    SERVICE_TIER = ServiceTier.CRITICAL
    SERVICE_PRIORITY = ServicePriority.CRITICAL
    DEFAULT_INTERVAL = 5.0
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.circuit_breaker = None
    
    async def on_start(self) -> None:
        """Initialize circuit breaker."""
        try:
            from trading_bot.risk.circuit_breaker import CircuitBreaker
            self.circuit_breaker = CircuitBreaker()
        except ImportError:
            logger.warning("Circuit breaker not available")
    
    async def execute(self) -> None:
        """Check circuit breaker status."""
        if not self.circuit_breaker:
            return
        
        try:
            if hasattr(self.circuit_breaker, 'is_open'):
                if self.circuit_breaker.is_open():
                    logger.warning("Circuit breaker is OPEN - trading halted")
            
            if hasattr(self.circuit_breaker, 'get_status'):
                status = self.circuit_breaker.get_status()
                logger.debug(f"Circuit breaker status: {status}")
                
        except Exception as e:
            logger.error(f"Circuit breaker monitoring error: {e}")


# =============================================================================
# TIER 2: LEARNING SERVICES
# =============================================================================

class MarketStudentService(BaseBackgroundService):
    """Learns from market data and trades."""
    
    SERVICE_NAME = "market_student"
    SERVICE_TIER = ServiceTier.LEARNING
    SERVICE_PRIORITY = ServicePriority.HIGH
    DEFAULT_INTERVAL = 300.0  # 5 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.orchestrator = None
    
    async def on_start(self) -> None:
        """Initialize market student."""
        try:
            from trading_bot.market_student.market_student_orchestrator import MarketStudentOrchestrator
            self.orchestrator = MarketStudentOrchestrator()
            logger.info("Market Student initialized")
        except ImportError as e:
            logger.warning(f"Market Student not available: {e}")
    
    async def execute(self) -> None:
        """Run learning cycle."""
        if not self.orchestrator:
            return
        
        try:
            if hasattr(self.orchestrator, 'learn_cycle'):
                await self.orchestrator.learn_cycle()
            elif hasattr(self.orchestrator, 'run_cycle'):
                await self.orchestrator.run_cycle()
            logger.debug("Market Student learning cycle completed")
        except Exception as e:
            logger.error(f"Market Student error: {e}")


class EternalEvolutionService(BaseBackgroundService):
    """Continuously evolves and improves the system."""
    
    SERVICE_NAME = "eternal_evolution"
    SERVICE_TIER = ServiceTier.LEARNING
    SERVICE_PRIORITY = ServicePriority.NORMAL
    DEFAULT_INTERVAL = 600.0  # 10 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.orchestrator = None
    
    async def on_start(self) -> None:
        """Initialize eternal evolution."""
        try:
            from trading_bot.eternal_evolution.eternal_orchestrator import EternalOrchestrator
            self.orchestrator = EternalOrchestrator()
            logger.info("Eternal Evolution initialized")
        except ImportError as e:
            logger.warning(f"Eternal Evolution not available: {e}")
    
    async def execute(self) -> None:
        """Run evolution cycle."""
        if not self.orchestrator:
            return
        
        try:
            if hasattr(self.orchestrator, 'evolve'):
                await self.orchestrator.evolve()
            elif hasattr(self.orchestrator, 'run_cycle'):
                await self.orchestrator.run_cycle()
            logger.debug("Eternal Evolution cycle completed")
        except Exception as e:
            logger.error(f"Eternal Evolution error: {e}")


class SelfDiagnosticService(BaseBackgroundService):
    """Runs self-diagnostics on the system."""
    
    SERVICE_NAME = "self_diagnostic"
    SERVICE_TIER = ServiceTier.LEARNING
    SERVICE_PRIORITY = ServicePriority.NORMAL
    DEFAULT_INTERVAL = 900.0  # 15 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.engine = None
    
    async def on_start(self) -> None:
        """Initialize diagnostic engine."""
        try:
            from trading_bot.self_diagnostic.diagnostic_engine import DiagnosticEngine
            self.engine = DiagnosticEngine()
            logger.info("Self-Diagnostic initialized")
        except ImportError as e:
            logger.warning(f"Self-Diagnostic not available: {e}")
    
    async def execute(self) -> None:
        """Run diagnostics."""
        if not self.engine:
            return
        
        try:
            if hasattr(self.engine, 'run_diagnostics'):
                results = await self.engine.run_diagnostics()
                if results:
                    logger.info(f"Diagnostics completed: {len(results)} checks")
            elif hasattr(self.engine, 'diagnose'):
                await self.engine.diagnose()
        except Exception as e:
            logger.error(f"Self-Diagnostic error: {e}")


class KnowledgeHarvesterService(BaseBackgroundService):
    """Harvests knowledge from external sources."""
    
    SERVICE_NAME = "knowledge_harvester"
    SERVICE_TIER = ServiceTier.LEARNING
    SERVICE_PRIORITY = ServicePriority.LOW
    DEFAULT_INTERVAL = 1800.0  # 30 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.harvester = None
    
    async def on_start(self) -> None:
        """Initialize knowledge harvester."""
        try:
            from trading_bot.sentient_core.knowledge_harvester import KnowledgeHarvester
            self.harvester = KnowledgeHarvester()
            logger.info("Knowledge Harvester initialized")
        except ImportError as e:
            logger.warning(f"Knowledge Harvester not available: {e}")
    
    async def execute(self) -> None:
        """Harvest knowledge."""
        if not self.harvester:
            return
        
        try:
            if hasattr(self.harvester, 'harvest'):
                await self.harvester.harvest()
            elif hasattr(self.harvester, 'run'):
                await self.harvester.run()
            logger.debug("Knowledge harvesting completed")
        except Exception as e:
            logger.error(f"Knowledge Harvester error: {e}")


# =============================================================================
# TIER 3: INTELLIGENCE SERVICES
# =============================================================================

class SentimentMonitorService(BaseBackgroundService):
    """Monitors market sentiment."""
    
    SERVICE_NAME = "sentiment_monitor"
    SERVICE_TIER = ServiceTier.INTELLIGENCE
    SERVICE_PRIORITY = ServicePriority.NORMAL
    DEFAULT_INTERVAL = 300.0  # 5 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.analyzer = None
        self.current_sentiment = None
    
    async def on_start(self) -> None:
        """Initialize sentiment analyzer."""
        try:
            from trading_bot.analysis.sentiment_analyzer import SentimentAnalyzer
            self.analyzer = SentimentAnalyzer()
            logger.info("Sentiment Monitor initialized")
        except ImportError as e:
            logger.warning(f"Sentiment Analyzer not available: {e}")
    
    async def execute(self) -> None:
        """Analyze sentiment."""
        if not self.analyzer:
            return
        
        try:
            if hasattr(self.analyzer, 'analyze'):
                self.current_sentiment = await self.analyzer.analyze()
            elif hasattr(self.analyzer, 'get_sentiment'):
                self.current_sentiment = self.analyzer.get_sentiment()
            
            if self.current_sentiment:
                logger.debug(f"Current sentiment: {self.current_sentiment}")
        except Exception as e:
            logger.error(f"Sentiment Monitor error: {e}")


class NewsCollectorService(BaseBackgroundService):
    """Collects and processes news."""
    
    SERVICE_NAME = "news_collector"
    SERVICE_TIER = ServiceTier.INTELLIGENCE
    SERVICE_PRIORITY = ServicePriority.NORMAL
    DEFAULT_INTERVAL = 600.0  # 10 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.collector = None
    
    async def on_start(self) -> None:
        """Initialize news collector."""
        try:
            from trading_bot.analysis.news_collector import NewsCollector
            self.collector = NewsCollector()
            logger.info("News Collector initialized")
        except ImportError as e:
            logger.warning(f"News Collector not available: {e}")
    
    async def execute(self) -> None:
        """Collect news."""
        if not self.collector:
            return
        
        try:
            if hasattr(self.collector, 'collect'):
                news = await self.collector.collect()
                if news:
                    logger.debug(f"Collected {len(news)} news items")
        except Exception as e:
            logger.error(f"News Collector error: {e}")


class RegimeDetectorService(BaseBackgroundService):
    """Detects market regime changes."""
    
    SERVICE_NAME = "regime_detector"
    SERVICE_TIER = ServiceTier.INTELLIGENCE
    SERVICE_PRIORITY = ServicePriority.HIGH
    DEFAULT_INTERVAL = 60.0  # 1 minute
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.detector = None
        self.current_regime = None
    
    async def on_start(self) -> None:
        """Initialize regime detector."""
        try:
            from trading_bot.analysis.market_regime_detector import MarketRegimeDetector
            self.detector = MarketRegimeDetector()
            logger.info("Regime Detector initialized")
        except ImportError as e:
            logger.warning(f"Regime Detector not available: {e}")
    
    async def execute(self) -> None:
        """Detect market regime."""
        if not self.detector:
            return
        
        try:
            if hasattr(self.detector, 'detect'):
                new_regime = await self.detector.detect()
                if new_regime != self.current_regime:
                    logger.info(f"Regime change detected: {self.current_regime} -> {new_regime}")
                    self.current_regime = new_regime
        except Exception as e:
            logger.error(f"Regime Detector error: {e}")


class CorrelationMonitorService(BaseBackgroundService):
    """Monitors asset correlations."""
    
    SERVICE_NAME = "correlation_monitor"
    SERVICE_TIER = ServiceTier.INTELLIGENCE
    SERVICE_PRIORITY = ServicePriority.NORMAL
    DEFAULT_INTERVAL = 300.0  # 5 minutes
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.monitor = None
    
    async def on_start(self) -> None:
        """Initialize correlation monitor."""
        try:
            from trading_bot.risk.realtime_correlation_monitor import RealtimeCorrelationMonitor
            self.monitor = RealtimeCorrelationMonitor()
            logger.info("Correlation Monitor initialized")
        except ImportError as e:
            logger.warning(f"Correlation Monitor not available: {e}")
    
    async def execute(self) -> None:
        """Monitor correlations."""
        if not self.monitor:
            return
        
        try:
            if hasattr(self.monitor, 'update'):
                await self.monitor.update()
            if hasattr(self.monitor, 'check_alerts'):
                alerts = self.monitor.check_alerts()
                if alerts:
                    logger.warning(f"Correlation alerts: {alerts}")
        except Exception as e:
            logger.error(f"Correlation Monitor error: {e}")


# =============================================================================
# TIER 4: OPTIMIZATION SERVICES
# =============================================================================

class PerformanceAnalyzerService(BaseBackgroundService):
    """Analyzes trading performance."""
    
    SERVICE_NAME = "performance_analyzer"
    SERVICE_TIER = ServiceTier.OPTIMIZATION
    SERVICE_PRIORITY = ServicePriority.NORMAL
    DEFAULT_INTERVAL = 3600.0  # 1 hour
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.analyzer = None
    
    async def on_start(self) -> None:
        """Initialize performance analyzer."""
        try:
            from trading_bot.monitoring.performance_monitor import PerformanceMonitor
            self.analyzer = PerformanceMonitor()
            logger.info("Performance Analyzer initialized")
        except ImportError as e:
            logger.warning(f"Performance Analyzer not available: {e}")
    
    async def execute(self) -> None:
        """Analyze performance."""
        if not self.analyzer:
            return
        
        try:
            if hasattr(self.analyzer, 'analyze'):
                report = await self.analyzer.analyze()
                if report:
                    logger.info(f"Performance report generated")
        except Exception as e:
            logger.error(f"Performance Analyzer error: {e}")


class StrategyOptimizerService(BaseBackgroundService):
    """Optimizes trading strategies."""
    
    SERVICE_NAME = "strategy_optimizer"
    SERVICE_TIER = ServiceTier.OPTIMIZATION
    SERVICE_PRIORITY = ServicePriority.LOW
    DEFAULT_INTERVAL = 7200.0  # 2 hours
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.optimizer = None
    
    async def on_start(self) -> None:
        """Initialize strategy optimizer."""
        try:
            from trading_bot.ml.strategy_optimizer import StrategyOptimizer
            self.optimizer = StrategyOptimizer()
            logger.info("Strategy Optimizer initialized")
        except ImportError as e:
            logger.warning(f"Strategy Optimizer not available: {e}")
    
    async def execute(self) -> None:
        """Run optimization."""
        if not self.optimizer:
            return
        
        try:
            if hasattr(self.optimizer, 'optimize'):
                results = await self.optimizer.optimize()
                if results:
                    logger.info(f"Strategy optimization completed")
        except Exception as e:
            logger.error(f"Strategy Optimizer error: {e}")


# =============================================================================
# TIER 5: MAINTENANCE SERVICES
# =============================================================================

class DataCleanupService(BaseBackgroundService):
    """Cleans up old data files."""
    
    SERVICE_NAME = "data_cleanup"
    SERVICE_TIER = ServiceTier.MAINTENANCE
    SERVICE_PRIORITY = ServicePriority.BACKGROUND
    DEFAULT_INTERVAL = 86400.0  # 24 hours
    
    async def execute(self) -> None:
        """Clean up old data."""
        try:
            # Clean old log files
            log_dir = Path('logs')
            if log_dir.exists():
                cutoff = datetime.now() - timedelta(days=30)
                for log_file in log_dir.glob('*.log.*'):
                    try:
                        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if mtime < cutoff:
                            log_file.unlink()
                            logger.debug(f"Deleted old log: {log_file}")
                    except Exception:
                        pass
            
            # Clean old reports
            report_dir = Path('reports')
            if report_dir.exists():
                cutoff = datetime.now() - timedelta(days=90)
                for report_file in report_dir.glob('*.json'):
                    try:
                        mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                        if mtime < cutoff:
                            report_file.unlink()
                            logger.debug(f"Deleted old report: {report_file}")
                    except Exception:
                        pass
            
            logger.info("Data cleanup completed")
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")


class LogRotationService(BaseBackgroundService):
    """Rotates log files."""
    
    SERVICE_NAME = "log_rotation"
    SERVICE_TIER = ServiceTier.MAINTENANCE
    SERVICE_PRIORITY = ServicePriority.BACKGROUND
    DEFAULT_INTERVAL = 3600.0  # 1 hour
    
    async def execute(self) -> None:
        """Rotate logs if needed."""
        try:
            log_dir = Path('logs')
            max_size = 50 * 1024 * 1024  # 50MB
            
            for log_file in log_dir.glob('*.log'):
                try:
                    if log_file.stat().st_size > max_size:
                        # Rotate
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        rotated = log_file.with_suffix(f'.log.{timestamp}')
                        log_file.rename(rotated)
                        logger.info(f"Rotated log: {log_file} -> {rotated}")
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Log rotation error: {e}")


class DatabaseMaintenanceService(BaseBackgroundService):
    """Maintains database health."""
    
    SERVICE_NAME = "database_maintenance"
    SERVICE_TIER = ServiceTier.MAINTENANCE
    SERVICE_PRIORITY = ServicePriority.BACKGROUND
    DEFAULT_INTERVAL = 86400.0  # 24 hours
    
    async def execute(self) -> None:
        """Run database maintenance."""
        try:
            import sqlite3
            
            # Find and vacuum SQLite databases
            for db_file in Path('.').rglob('*.db'):
                try:
                    conn = sqlite3.connect(str(db_file))
                    conn.execute('VACUUM')
                    conn.close()
                    logger.debug(f"Vacuumed database: {db_file}")
                except Exception:
                    pass
            
            logger.info("Database maintenance completed")
        except Exception as e:
            logger.error(f"Database maintenance error: {e}")


# =============================================================================
# BACKGROUND SERVICES MANAGER
# =============================================================================

class BackgroundServicesManager:
    """
    Manages all background services.
    
    This is the main orchestrator for background services that:
    1. Initializes services by tier
    2. Manages service lifecycle
    3. Monitors service health
    4. Handles graceful shutdown
    """
    
    # All available services
    SERVICE_CLASSES = {
        # Tier 1: Critical
        'system_health_monitor': SystemHealthMonitor,
        'risk_monitor': RiskMonitorService,
        'circuit_breaker_monitor': CircuitBreakerMonitor,
        
        # Tier 2: Learning
        'market_student': MarketStudentService,
        'eternal_evolution': EternalEvolutionService,
        'self_diagnostic': SelfDiagnosticService,
        'knowledge_harvester': KnowledgeHarvesterService,
        
        # Tier 3: Intelligence
        'sentiment_monitor': SentimentMonitorService,
        'news_collector': NewsCollectorService,
        'regime_detector': RegimeDetectorService,
        'correlation_monitor': CorrelationMonitorService,
        
        # Tier 4: Optimization
        'performance_analyzer': PerformanceAnalyzerService,
        'strategy_optimizer': StrategyOptimizerService,
        
        # Tier 5: Maintenance
        'data_cleanup': DataCleanupService,
        'log_rotation': LogRotationService,
        'database_maintenance': DatabaseMaintenanceService,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.services: Dict[str, BaseBackgroundService] = {}
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        logger.info("BackgroundServicesManager initialized")
    
    async def initialize(self, tiers: Optional[List[int]] = None, 
                        services: Optional[List[str]] = None) -> None:
        """Initialize services."""
        logger.info("=" * 60)
        logger.info("INITIALIZING BACKGROUND SERVICES")
        logger.info("=" * 60)
        
        # Determine which services to start
        services_to_start = []
        
        if services:
            # Specific services requested
            services_to_start = services
        elif tiers:
            # Specific tiers requested
            for name, cls in self.SERVICE_CLASSES.items():
                if cls.SERVICE_TIER.value in tiers:
                    services_to_start.append(name)
        else:
            # All services
            services_to_start = list(self.SERVICE_CLASSES.keys())
        
        # Initialize services
        for name in services_to_start:
            if name in self.SERVICE_CLASSES:
                try:
                    service_config = self.config.get(name, {})
                    service = self.SERVICE_CLASSES[name](service_config)
                    self.services[name] = service
                    logger.info(f"  ✓ {name} (Tier {service.SERVICE_TIER.value})")
                except Exception as e:
                    logger.error(f"  ✗ {name}: {e}")
        
        logger.info(f"Initialized {len(self.services)} services")
        logger.info("=" * 60)
    
    async def start(self) -> None:
        """Start all services."""
        if self.running:
            logger.warning("Services already running")
            return
        
        self.running = True
        logger.info("Starting background services...")
        
        # Start services by tier (critical first)
        for tier in ServiceTier:
            tier_services = [
                (name, svc) for name, svc in self.services.items()
                if svc.SERVICE_TIER == tier
            ]
            
            if tier_services:
                logger.info(f"Starting Tier {tier.value} ({tier.name}) services...")
                for name, service in tier_services:
                    try:
                        await service.start()
                        logger.info(f"  ✓ {name} started")
                    except Exception as e:
                        logger.error(f"  ✗ {name} failed: {e}")
        
        logger.info("All services started")
    
    async def stop(self) -> None:
        """Stop all services."""
        if not self.running:
            return
        
        logger.info("Stopping background services...")
        self.running = False
        self.shutdown_event.set()
        
        # Stop services in reverse tier order (maintenance first, critical last)
        for tier in reversed(list(ServiceTier)):
            tier_services = [
                (name, svc) for name, svc in self.services.items()
                if svc.SERVICE_TIER == tier
            ]
            
            for name, service in tier_services:
                try:
                    await service.stop()
                    logger.info(f"  ✓ {name} stopped")
                except Exception as e:
                    logger.error(f"  ✗ {name} stop failed: {e}")
        
        logger.info("All services stopped")
    
    async def run(self) -> None:
        """Run the services manager."""
        await self.start()
        
        try:
            # Wait for shutdown signal
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        return {
            'running': self.running,
            'service_count': len(self.services),
            'services': {
                name: svc.get_status()
                for name, svc in self.services.items()
            }
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get health of all services."""
        healthy_count = sum(
            1 for svc in self.services.values()
            if svc.health.healthy
        )
        
        return {
            'healthy': healthy_count == len(self.services),
            'healthy_count': healthy_count,
            'total_count': len(self.services),
            'services': {
                name: {
                    'healthy': svc.health.healthy,
                    'message': svc.health.message,
                    'error_count': svc.health.error_count
                }
                for name, svc in self.services.items()
            }
        }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='AlphaAlgo Background Services Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--tier', '-t',
        type=str,
        help='Comma-separated list of tiers to run (1-5)'
    )
    
    parser.add_argument(
        '--service', '-s',
        type=str,
        help='Comma-separated list of specific services to run'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available services'
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
    
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # List services
    if args.list:
        print("\nAvailable Background Services:")
        print("=" * 60)
        for tier in ServiceTier:
            print(f"\nTier {tier.value}: {tier.name}")
            print("-" * 40)
            for name, cls in BackgroundServicesManager.SERVICE_CLASSES.items():
                if cls.SERVICE_TIER == tier:
                    print(f"  • {name}")
                    print(f"    Priority: {cls.SERVICE_PRIORITY.name}")
                    print(f"    Interval: {cls.DEFAULT_INTERVAL}s")
        return
    
    # Parse tiers
    tiers = None
    if args.tier:
        tiers = [int(t.strip()) for t in args.tier.split(',')]
    
    # Parse services
    services = None
    if args.service:
        services = [s.strip() for s in args.service.split(',')]
    
    # Create manager
    manager = BackgroundServicesManager()
    
    # Initialize
    await manager.initialize(tiers=tiers, services=services)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        manager.shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    await manager.run()


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ALPHAALGO BACKGROUND SERVICES                            ║
    ║                                                               ║
    ║     Tier 1: Critical Services (Health, Risk, Circuit)        ║
    ║     Tier 2: Learning Services (Student, Evolution)           ║
    ║     Tier 3: Intelligence Services (Sentiment, News)          ║
    ║     Tier 4: Optimization Services (Performance, Strategy)    ║
    ║     Tier 5: Maintenance Services (Cleanup, Logs, DB)         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
