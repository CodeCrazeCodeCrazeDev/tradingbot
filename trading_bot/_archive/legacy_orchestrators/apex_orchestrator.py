"""
APEX-FI Orchestrator
====================

Master orchestrator that coordinates all 7 layers of APEX-FI.

Genetic Parentage: Palantir × Two Sigma × Citadel
Architecture Class: Self-Improving · Self-Discovering · Self-Evolving
Constitutional Version: 4.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SystemState(str, Enum):
    """APEX-FI system states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    HALTED = "halted"
    ERROR = "error"


@dataclass
class PerformanceMetrics:
    """System-wide performance metrics."""
    
    # Performance
    sharpe_ratio: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    total_pnl: float = 0.0
    
    # Discovery
    active_factors: int = 0
    candidates_generated_today: int = 0
    candidates_validated_today: int = 0
    
    # Operations
    data_sources_active: int = 0
    models_in_parliament: int = 0
    strategies_active: int = 0
    
    # Latency (milliseconds)
    avg_signal_latency_ms: float = 0.0
    avg_execution_latency_ms: float = 0.0
    avg_risk_check_latency_ms: float = 0.0
    
    # Evolution
    self_modifications_deployed: int = 0
    sandbox_candidates: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'sharpe_ratio': self.sharpe_ratio,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'total_pnl': self.total_pnl,
            'active_factors': self.active_factors,
            'candidates_generated_today': self.candidates_generated_today,
            'candidates_validated_today': self.candidates_validated_today,
            'data_sources_active': self.data_sources_active,
            'models_in_parliament': self.models_in_parliament,
            'strategies_active': self.strategies_active,
            'avg_signal_latency_ms': self.avg_signal_latency_ms,
            'avg_execution_latency_ms': self.avg_execution_latency_ms,
            'avg_risk_check_latency_ms': self.avg_risk_check_latency_ms,
            'self_modifications_deployed': self.self_modifications_deployed,
            'sandbox_candidates': self.sandbox_candidates,
        }


class APEXOrchestrator:
    """
    APEX-FI Master Orchestrator.
    
    Coordinates all 7 layers:
    1. Data Fabric & Ontology Engine
    2. Alpha Mining Engine
    3. Model Parliament
    4. Portfolio Architect
    5. Execution Intelligence
    6. Risk Governance
    7. Meta-Intelligence
    
    Plus the Constitutional Layer for immutable governance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.state = SystemState.UNINITIALIZED
        self._start_time: Optional[datetime] = None
        self._initialization_complete = False
        
        # Layer references (initialized during startup)
        self._constitutional_layer = None
        self._data_fabric = None
        self._alpha_mining = None
        self._model_parliament = None
        self._portfolio_architect = None
        self._execution_intelligence = None
        self._risk_governance = None
        self._meta_intelligence = None
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        
        logger.info("=" * 60)
        logger.info("APEX-FI Orchestrator Initialized")
        logger.info("Genetic Parentage: Palantir × Two Sigma × Citadel")
        logger.info("Constitutional Version: 4.0")
        logger.info("=" * 60)
    
    async def initialize(self) -> bool:
        """
        Run the initialization sequence.
        
        Returns:
            True if initialization successful
        """
        self.state = SystemState.INITIALIZING
        logger.info("Starting APEX-FI initialization sequence...")
        
        try:
            # Step 1: Constitutional Layer Verification
            logger.info("Step 1/8: Loading Constitutional Layer...")
            from .constitutional_layer import get_constitutional_layer
            self._constitutional_layer = get_constitutional_layer()
            
            # Verify constitutional constraints are immutable
            const_status = self._constitutional_layer.get_status()
            logger.info(f"Constitutional constraints verified: {const_status}")
            
            # Step 2: Data Fabric & Ontology Bootstrap
            logger.info("Step 2/8: Initializing Data Fabric...")
            from .layer1_data_fabric import DataFabric
            self._data_fabric = DataFabric()
            logger.info("✓ Data Fabric initialized")
            
            # Step 3: Alpha Mining Engine
            logger.info("Step 3/8: Initializing Alpha Mining Engine...")
            from .layer2_alpha_mining import AlphaMiningEngine
            self._alpha_mining = AlphaMiningEngine(self.config.get('alpha_mining', {}))
            self._alpha_mining.initialize()
            logger.info("✓ Alpha Mining Engine initialized")
            
            # Step 4: Model Parliament
            logger.info("Step 4/8: Initializing Model Parliament...")
            from .layer3_model_parliament import AdaptiveModelEnsemble
            self._model_parliament = AdaptiveModelEnsemble(self.config.get('model_parliament', {}))
            logger.info("✓ Model Parliament initialized")
            
            # Step 5: Portfolio Architect
            logger.info("Step 5/8: Initializing Portfolio Architect...")
            from .layer4_portfolio_architect import PortfolioArchitect
            self._portfolio_architect = PortfolioArchitect(self.config.get('portfolio', {}))
            logger.info("✓ Portfolio Architect initialized")
            
            # Step 6: Execution Intelligence
            logger.info("Step 6/8: Initializing Execution Intelligence...")
            from .layer5_execution_intelligence import ExecutionIntelligence
            self._execution_intelligence = ExecutionIntelligence(self.config.get('execution', {}))
            logger.info("✓ Execution Intelligence initialized")
            
            # Step 7: Risk Governance
            logger.info("Step 7/8: Initializing Risk Governance...")
            from .layer6_risk_governance import RiskGovernance
            self._risk_governance = RiskGovernance(self.config.get('risk', {}))
            logger.info("✓ Risk Governance initialized")
            
            # Step 8: Meta-Intelligence
            logger.info("Step 8/8: Initializing Meta-Intelligence...")
            from .layer7_meta_intelligence import MetaIntelligence
            self._meta_intelligence = MetaIntelligence(self.config.get('meta_intelligence', {}))
            logger.info("✓ Meta-Intelligence initialized - APEX LAYER ACTIVE")
            
            self._initialization_complete = True
            self.state = SystemState.READY
            
            logger.info("=" * 60)
            logger.info("APEX-FI Initialization Complete")
            logger.info("System State: READY")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state = SystemState.ERROR
            return False
    
    async def start(self) -> bool:
        """
        Start APEX-FI operation.
        
        Returns:
            True if started successfully
        """
        if not self._initialization_complete:
            logger.error("Cannot start - initialization not complete")
            return False
        
        if self._constitutional_layer.is_circuit_breaker_active():
            logger.error("Cannot start - circuit breaker is active")
            return False
        
        logger.info("Starting APEX-FI operation...")
        
        try:
            self.state = SystemState.RUNNING
            self._start_time = datetime.now()
            
            # Start Layer 1: Data Fabric
            if self._data_fabric:
                await self._data_fabric.start()
            
            # Start Layer 2: Alpha Mining
            if self._alpha_mining:
                await self._alpha_mining.start()
            
            # Start other layers when implemented
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
            logger.info("=" * 60)
            logger.info("APEX-FI OPERATIONAL")
            logger.info("System State: RUNNING")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Start failed: {e}")
            self.state = SystemState.ERROR
            return False
    
    async def stop(self) -> None:
        """Stop APEX-FI operation."""
        logger.info("Stopping APEX-FI...")
        
        # Stop all layers
        if self._alpha_mining:
            await self._alpha_mining.stop()
        
        if self._data_fabric:
            await self._data_fabric.stop()
        
        self.state = SystemState.HALTED
        logger.info("APEX-FI stopped")
    
    async def _monitoring_loop(self) -> None:
        """Continuous monitoring and metrics collection."""
        while self.state == SystemState.RUNNING:
            try:
                # Update metrics
                await self._update_metrics()
                
                # Check constitutional constraints
                await self._check_constraints()
                
                # Check system health
                await self._check_health()
                
                await asyncio.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _update_metrics(self) -> None:
        """Update performance metrics."""
        # Data Fabric metrics
        if self._data_fabric:
            df_status = self._data_fabric.get_status()
            self.metrics.data_sources_active = df_status['data_sources']
        
        # Alpha Mining metrics
        if self._alpha_mining:
            am_status = self._alpha_mining.get_status()
            self.metrics.active_factors = am_status['factor_library']['total_active_factors']
            self.metrics.candidates_generated_today = am_status['candidates_generated_today']
            self.metrics.candidates_validated_today = am_status['candidates_validated_today']
    
    async def _check_constraints(self) -> None:
        """Check constitutional constraints."""
        if not self._constitutional_layer:
            return
        
        # Check if circuit breaker activated
        if self._constitutional_layer.is_circuit_breaker_active():
            logger.critical("CIRCUIT BREAKER ACTIVE - Halting system")
            self.state = SystemState.HALTED
            await self.stop()
    
    async def _check_health(self) -> None:
        """Check system health."""
        # Check each layer's health
        unhealthy_layers = []
        
        if self._data_fabric and not self._data_fabric._running:
            unhealthy_layers.append("Data Fabric")
        
        if self._alpha_mining and not self._alpha_mining._running:
            unhealthy_layers.append("Alpha Mining")
        
        if unhealthy_layers:
            logger.warning(f"Unhealthy layers detected: {unhealthy_layers}")
            self.state = SystemState.DEGRADED
        elif self.state == SystemState.DEGRADED:
            # Recovered
            logger.info("System health recovered")
            self.state = SystemState.RUNNING
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        uptime_seconds = 0
        if self._start_time:
            uptime_seconds = (datetime.now() - self._start_time).total_seconds()
        
        status = {
            'state': self.state.value,
            'uptime_seconds': uptime_seconds,
            'initialization_complete': self._initialization_complete,
            'metrics': self.metrics.to_dict(),
        }
        
        # Layer statuses
        if self._constitutional_layer:
            status['constitutional_layer'] = self._constitutional_layer.get_status()
        
        if self._data_fabric:
            status['data_fabric'] = self._data_fabric.get_status()
        
        if self._alpha_mining:
            status['alpha_mining'] = self._alpha_mining.get_status()
        
        return status
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_state': self.state.value,
            'performance_metrics': self.metrics.to_dict(),
            'constitutional_status': self._constitutional_layer.get_status() if self._constitutional_layer else {},
            'north_star_targets': {
                'sharpe_ratio_target': 3.5,
                'sharpe_ratio_actual': self.metrics.sharpe_ratio,
                'max_drawdown_limit': 0.08,
                'max_drawdown_actual': self.metrics.max_drawdown,
                'alpha_hypotheses_target_per_day': 100,
                'alpha_hypotheses_actual': self.metrics.candidates_generated_today,
                'active_factors_target': 50000,
                'active_factors_actual': self.metrics.active_factors,
            }
        }


# Singleton instance
_apex_orchestrator: Optional[APEXOrchestrator] = None


def get_apex_orchestrator(config: Optional[Dict[str, Any]] = None) -> APEXOrchestrator:
    """Get the singleton APEX Orchestrator."""
    global _apex_orchestrator
    if _apex_orchestrator is None:
        _apex_orchestrator = APEXOrchestrator(config=config)
    return _apex_orchestrator


async def quick_start(config: Optional[Dict[str, Any]] = None) -> APEXOrchestrator:
    """
    Quick start APEX-FI.
    
    Initializes and starts the system in one call.
    """
    logger.info("APEX-FI Quick Start initiated...")
    
    apex = get_apex_orchestrator(config)
    
    # Initialize
    init_success = await apex.initialize()
    if not init_success:
        raise RuntimeError("APEX-FI initialization failed")
    
    # Start
    start_success = await apex.start()
    if not start_success:
        raise RuntimeError("APEX-FI start failed")
    
    logger.info("APEX-FI Quick Start complete - System operational")
    
    return apex
