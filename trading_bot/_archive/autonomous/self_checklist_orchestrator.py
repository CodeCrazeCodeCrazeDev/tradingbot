"""
Self-Checklist Orchestrator - Unified Self-Assessment System

Orchestrates all self-checklist components into a comprehensive
self-assessment framework for continuous bot self-evaluation.

Author: Trading Bot Team
Date: 2025-10-23
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

from trading_bot.autonomous.self_checklist_core import (
    SelfStateReflection, SelfContextRecognition, SelfConfidenceEstimation,
    SelfExplainability, SelfMoodIndex, SelfMemorySystem, SelfBudgeting,
    SelfBenchmarking
)
from trading_bot.autonomous.self_checklist_advanced import (
    SelfRetrainingOnDrift, SelfEvolvingStrategies, SelfTuningParameters,
    SelfBacktestingValidator, SelfCalibrationCheck, SelfConsistencyMonitor,
    SelfRealityAlignment, SelfCircuitBreaker, SelfRollback, SelfPatch,
    SelfSandboxMode, SelfBackupRestore, SelfSecurityScan,
    SelfRewardFunctionAdjustment
)
from trading_bot.autonomous.self_checklist_extended import (
    SelfStrategyGeneration, SelfKnowledgeGraph, SelfMetaLearning,
    SelfObservationLoop, SelfRiskGovernance, SelfPruning, SelfAuditTrails,
    SelfCrossValidation, SelfRestart, SelfIsolation, SelfLatencyControl,
    SelfMultiMarketAwareness, SelfAgentCollaboration, SelfInfrastructureScaling,
    SelfReflectiveMetaAgent, SelfSupervisedLearningEngine, SelfStrategyMarketplace
)

logger = logging.getLogger(__name__)


class SelfChecklistStatus(Enum):
    EXCELLENT = "excellent"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SelfChecklistReport:
    """Comprehensive self-checklist report"""
    timestamp: datetime = field(default_factory=datetime.now)
    overall_status: SelfChecklistStatus = SelfChecklistStatus.HEALTHY
    overall_score: float = 0.0
    items: List[Dict[str, Any]] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    category_scores: Dict[str, float] = field(default_factory=dict)


class SelfChecklistOrchestrator:
    """Orchestrates all self-checklist components"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Core components
        self.state_reflection = SelfStateReflection()
        self.context_recognition = SelfContextRecognition()
        self.confidence_estimation = SelfConfidenceEstimation()
        self.explainability = SelfExplainability()
        self.mood_index = SelfMoodIndex()
        self.memory_system = SelfMemorySystem()
        self.budgeting = SelfBudgeting()
        self.benchmarking = SelfBenchmarking()
        
        # Advanced components
        self.drift_detection = SelfRetrainingOnDrift()
        self.strategy_evolution = SelfEvolvingStrategies()
        self.parameter_tuning = SelfTuningParameters()
        self.backtesting = SelfBacktestingValidator()
        self.calibration = SelfCalibrationCheck()
        self.consistency = SelfConsistencyMonitor()
        self.reality_alignment = SelfRealityAlignment()
        self.circuit_breaker = SelfCircuitBreaker()
        self.rollback = SelfRollback()
        self.patch_system = SelfPatch()
        self.sandbox = SelfSandboxMode()
        self.backup_restore = SelfBackupRestore()
        self.security = SelfSecurityScan()
        self.reward_adjustment = SelfRewardFunctionAdjustment()
        
        # Extended components
        self.strategy_generation = SelfStrategyGeneration()
        self.knowledge_graph = SelfKnowledgeGraph()
        self.meta_learning = SelfMetaLearning()
        self.observation_loop = SelfObservationLoop()
        self.risk_governance = SelfRiskGovernance()
        self.pruning = SelfPruning()
        self.audit_trails = SelfAuditTrails()
        self.cross_validation = SelfCrossValidation()
        self.restart = SelfRestart()
        self.isolation = SelfIsolation()
        self.latency_control = SelfLatencyControl()
        self.multi_market = SelfMultiMarketAwareness()
        self.agent_collaboration = SelfAgentCollaboration()
        self.infrastructure_scaling = SelfInfrastructureScaling()
        self.reflective_meta_agent = SelfReflectiveMetaAgent()
        self.supervised_learning = SelfSupervisedLearningEngine()
        self.strategy_marketplace = SelfStrategyMarketplace()
        
        # History
        self.checklist_history = deque(maxlen=100)
        
        logger.info("Self-Checklist Orchestrator initialized")
    
    async def run_full_checklist(self) -> SelfChecklistReport:
        """Run complete self-checklist"""
        logger.info("Running full self-checklist...")
        
        report = SelfChecklistReport()
        
        # Core checks
        core_items = await self._run_core_checks()
        
        # Advanced checks
        advanced_items = await self._run_advanced_checks()
        
        # Extended checks
        extended_items = await self._run_extended_checks()
        
        # Combine all items
        all_items = core_items + advanced_items + extended_items
        report.items = [
            {
                "name": item.name,
                "status": item.status.value,
                "score": item.score,
                "details": item.details,
                "timestamp": item.timestamp.isoformat()
            }
            for item in all_items
        ]
        
        # Calculate overall score
        scores = [item.score for item in all_items]
        report.overall_score = sum(scores) / len(scores) if scores else 0
        
        # Determine overall status
        if report.overall_score >= 90:
            report.overall_status = SelfChecklistStatus.EXCELLENT
        elif report.overall_score >= 75:
            report.overall_status = SelfChecklistStatus.HEALTHY
        elif report.overall_score >= 50:
            report.overall_status = SelfChecklistStatus.WARNING
        else:
            report.overall_status = SelfChecklistStatus.CRITICAL
        
        # Calculate category scores
        report.category_scores = {
            "core": sum(item.score for item in core_items) / len(core_items) if core_items else 0,
            "advanced": sum(item.score for item in advanced_items) / len(advanced_items) if advanced_items else 0,
            "extended": sum(item.score for item in extended_items) / len(extended_items) if extended_items else 0,
        }
        
        # Identify critical issues
        report.critical_issues = [
            item.name for item in all_items
            if item.status.value == "critical" or item.score < 30
        ]
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(all_items)
        
        # Store in history
        self.checklist_history.append(report)
        
        logger.info(f"Self-checklist completed: {report.overall_status.value} ({report.overall_score:.1f}%)")
        
        return report
    
    async def _run_core_checks(self) -> List:
        """Run core self-checks"""
        return await asyncio.gather(
            self.state_reflection.reflect_on_state(),
            self.context_recognition.recognize_context(),
            self.confidence_estimation.estimate_confidence(),
            self.explainability.check_explainability(),
            self.mood_index.calculate_mood(),
            self.memory_system.check_memory(),
            self.budgeting.check_budget(),
            self.benchmarking.benchmark_performance()
        )
    
    async def _run_advanced_checks(self) -> List:
        """Run advanced self-checks"""
        return await asyncio.gather(
            self.drift_detection.detect_and_retrain(),
            self.strategy_evolution.evolve_strategies(),
            self.parameter_tuning.tune_parameters(),
            self.backtesting.validate_through_backtesting(),
            self.calibration.check_calibration(),
            self.consistency.monitor_consistency(),
            self.reality_alignment.check_reality_alignment(),
            self.circuit_breaker.check_circuit_breaker(),
            self.rollback.check_rollback_capability(),
            self.patch_system.check_patch_system(),
            self.sandbox.check_sandbox_mode(),
            self.backup_restore.check_backup_restore(),
            self.security.run_security_scan(),
            self.reward_adjustment.check_reward_adjustment()
        )
    
    async def _run_extended_checks(self) -> List:
        """Run extended self-checks"""
        return await asyncio.gather(
            self.strategy_generation.check_strategy_generation(),
            self.knowledge_graph.check_knowledge_graph(),
            self.meta_learning.check_meta_learning(),
            self.observation_loop.check_observation_loop(),
            self.risk_governance.check_risk_governance(),
            self.pruning.check_pruning(),
            self.audit_trails.check_audit_trails(),
            self.cross_validation.check_cross_validation(),
            self.restart.check_restart_capability(),
            self.isolation.check_isolation(),
            self.latency_control.check_latency_control(),
            self.multi_market.check_multi_market_awareness(),
            self.agent_collaboration.check_agent_collaboration(),
            self.infrastructure_scaling.check_infrastructure_scaling(),
            self.reflective_meta_agent.check_reflective_meta_agent(),
            self.supervised_learning.check_supervised_learning(),
            self.strategy_marketplace.check_strategy_marketplace()
        )
    
    def _generate_recommendations(self, items: List) -> List[str]:
        """Generate recommendations based on checklist results"""
        recommendations = []
        
        for item in items:
            if item.score < 70:
                recommendations.append(f"Improve {item.name} (current: {item.score:.1f}%)")
        
        return recommendations[:10]  # Top 10 recommendations
    
    async def run_quick_checklist(self) -> SelfChecklistReport:
        """Run quick checklist (core components only)"""
        logger.info("Running quick self-checklist...")
        
        report = SelfChecklistReport()
        items = await self._run_core_checks()
        
        report.items = [
            {
                "name": item.name,
                "status": item.status.value,
                "score": item.score
            }
            for item in items
        ]
        
        scores = [item.score for item in items]
        report.overall_score = sum(scores) / len(scores) if scores else 0
        
        if report.overall_score >= 75:
            report.overall_status = SelfChecklistStatus.HEALTHY
        else:
            report.overall_status = SelfChecklistStatus.WARNING
        
        return report
    
    def get_latest_report(self) -> Optional[SelfChecklistReport]:
        """Get latest checklist report"""
        return self.checklist_history[-1] if self.checklist_history else None
    
    def get_checklist_summary(self) -> Dict[str, Any]:
        """Get summary of checklist status"""
        latest = self.get_latest_report()
        
        if not latest:
            return {
                "status": "UNKNOWN",
                "score": 0,
                "items_checked": 0,
                "critical_issues": 0
            }
        
        return {
            "status": latest.overall_status.value,
            "score": latest.overall_score,
            "items_checked": len(latest.items),
            "critical_issues": len(latest.critical_issues),
            "category_scores": latest.category_scores,
            "timestamp": latest.timestamp.isoformat()
        }


# Singleton instance
_self_checklist_orchestrator = None


def get_self_checklist_orchestrator(config: Optional[Dict] = None) -> SelfChecklistOrchestrator:
    """Get or create singleton orchestrator"""
    global _self_checklist_orchestrator
    if _self_checklist_orchestrator is None:
        _self_checklist_orchestrator = SelfChecklistOrchestrator(config)
    return _self_checklist_orchestrator


async def run_full_checklist() -> SelfChecklistReport:
    """Run full self-checklist"""
    orchestrator = get_self_checklist_orchestrator()
    return await orchestrator.run_full_checklist()


async def run_quick_checklist() -> SelfChecklistReport:
    """Run quick self-checklist"""
    orchestrator = get_self_checklist_orchestrator()
    return await orchestrator.run_quick_checklist()


def get_checklist_summary() -> Dict[str, Any]:
    """Get checklist summary"""
    orchestrator = get_self_checklist_orchestrator()
    return orchestrator.get_checklist_summary()
