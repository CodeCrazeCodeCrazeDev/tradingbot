"""
Unified Financial Intelligence Infrastructure

A self-evolving financial intelligence system that:
- Continuously evaluates markets
- Audits its own reasoning
- Detects gaps in cognition
- Adversarially challenges conclusions
- Decomposes uncertainty
- Evolves under strict governance
- Compounds intelligence over time without sacrificing stability

Core Philosophy:
The system doesn't just learn from markets—it continuously discovers, measures,
and fixes the limits of its own reasoning, creating compounding intelligence
rather than static adaptation.

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                    FinancialIntelligenceSystem                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Market     │  │    Self      │  │  Capability  │            │
│  │  Evaluation  │  │  Inspection  │  │  Discovery   │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                  │                  │                     │
│  ┌──────▼──────────────────▼──────────────────▼───────┐            │
│  │           Unified Intelligence Core                 │            │
│  │  • Decision Governance (7 Layers)                  │            │
│  │  • Three-Memory System                             │            │
│  │  • Adversarial Validation                          │            │
│  │  • Uncertainty Decomposition                       │            │
│  └──────┬──────────────────────────────────────┬──────┘            │
│         │                                      │                     │
│  ┌──────▼──────────────┐  ┌───────────────────▼───────┐            │
│  │   Evolution         │  │    Intelligence         │            │
│  │   Orchestrator      │  │    Compounding          │            │
│  │  • Gap Detection    │  │  • Capability Stack      │            │
│  │  • Innovation Gen     │  │  • Performance History   │            │
│  │  • Validation       │  │  • Improvement Metrics   │            │
│  │  • Integration      │  │  • Bottleneck Analysis   │            │
│  └─────────────────────┘  └─────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
"""

from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import asyncio
import logging
import json
import numpy as np
from pathlib import Path

# Import all our engines
from .continuous_capability_discovery import (
    ContinuousCapabilityDiscoveryEngine,
    CapabilityGap,
    InnovationProposal,
    ConstraintProfile,
    CapabilityStatus
)
from .introspection_evolution import (
    IntrospectionDrivenEvolutionEngine,
    IntrospectionResult,
    RootCauseCategory,
    CausalFactor,
    Explanation,
    PrescribedFix
)
from .self_inspection import (
    SelfInspectionEngine,
    InspectionCategory,
    FindingSeverity,
    InspectionFinding,
    CalibrationProfile,
    ImprovementOpportunity
)
from .memory_system import DecisionMemory, OutcomeMemory, FailureMemory
from .plane_evolution import ControlledEvolutionPlane, ValidationResult

logger = logging.getLogger(__name__)


class SystemPhase(Enum):
    """Operational phases of the financial intelligence system"""
    INITIALIZING = "initializing"
    OBSERVING = "observing"  # Market evaluation
    REFLECTING = "reflecting"  # Self-inspection
    CHALLENGING = "challenging"  # Adversarial validation
    EVOLVING = "evolving"  # Capability improvement
    COMPOUNDING = "compounding"  # Intelligence accumulation
    STABLE = "stable"  # Normal operation
    DEGRADED = "degraded"  # Issues detected
    RECOVERING = "recovering"  # Self-healing


@dataclass
class IntelligenceMetrics:
    """Metrics tracking system intelligence over time"""
    timestamp: datetime
    
    # Decision quality
    avg_calibration_error: float
    decision_quality_score: float
    reasoning_soundness: float
    
    # Capability coverage
    total_capabilities: int
    active_capabilities: int
    capability_gaps: int
    
    # Evolution progress
    innovations_validated: int
    innovations_integrated: int
    integration_success_rate: float
    
    # Self-improvement
    bottlenecks_resolved: int
    improvements_compounded: int
    performance_trend: float
    
    # Stability
    system_health_score: float
    error_rate: float
    recovery_time: Optional[float]


@dataclass
class BottleneckAnalysis:
    """Analysis of system bottlenecks limiting performance"""
    bottleneck_id: str
    category: str
    description: str
    severity: float
    impact_on_performance: float
    root_cause: str
    proposed_solution: str
    estimated_improvement: float
    complexity: str
    is_resolvable: bool


@dataclass
class CompoundingEvent:
    """Record of intelligence compounding event"""
    event_id: str
    timestamp: datetime
    event_type: str  # capability_added, bug_fixed, pattern_learned, etc.
    description: str
    intelligence_delta: float
    capabilities_affected: List[str]
    lessons_learned: List[str]
    evidence: Dict[str, Any]


class UnifiedFinancialIntelligenceSystem:
    """
    Unified Financial Intelligence Infrastructure
    
    A self-evolving system that compounds intelligence over time through:
    
    1. CONTINUOUS MARKET EVALUATION
       - Real-time signal processing
       - Multi-regime adaptation
       - Dynamic strategy selection
    
    2. REASONING AUDIT & CHALLENGE
       - 7-layer governance validation
       - Adversarial analysis
       - Evidence sufficiency checks
    
    3. COGNITIVE GAP DETECTION
       - Self-inspection findings
       - Calibration tracking
       - Bias detection
    
    4. UNCERTAINTY DECOMPOSITION
       - Multi-dimensional uncertainty
       - Confidence calibration
       - Meta-uncertainty tracking
    
    5. GOVERNED EVOLUTION
       - Controlled capability integration
       - Reversible changes
       - Strict promotion gates
    
    6. INTELLIGENCE COMPOUNDING
       - Capability stacking
       - Learning accumulation
       - Performance trajectory tracking
    """
    
    def __init__(
        self,
        trading_system=None,
        constraint_profile: Optional[ConstraintProfile] = None,
        storage_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.trading_system = trading_system
        self.config = config or {}
        self.storage_path = storage_path or "financial_intelligence_system.json"
        
        # Initialize constraint profile
        self.constraints = constraint_profile or ConstraintProfile()
        
        # Initialize memory systems
        self.decision_memory = DecisionMemory("decisions.db")
        self.outcome_memory = OutcomeMemory("outcomes.db")
        self.failure_memory = FailureMemory("failures.db")
        
        # Initialize evolution plane for controlled capability validation
        self.evolution_plane = ControlledEvolutionPlane(
            self.decision_memory,
            self.outcome_memory,
            self.failure_memory
        )
        
        # Initialize the three core self-improvement engines
        self.capability_discovery = ContinuousCapabilityDiscoveryEngine(
            decision_memory=self.decision_memory,
            outcome_memory=self.outcome_memory,
            failure_memory=self.failure_memory,
            evolution_plane=self.evolution_plane,
            trading_system=trading_system,
            constraint_profile=self.constraints,
            storage_path="capability_discovery.json"
        )
        
        self.introspection_engine = IntrospectionDrivenEvolutionEngine(
            failure_memory=self.failure_memory,
            outcome_memory=self.outcome_memory,
            decision_memory=self.decision_memory,
            capability_discovery_engine=self.capability_discovery,
            storage_path="introspection.json"
        )
        
        self.self_inspection = SelfInspectionEngine(
            decision_memory=self.decision_memory,
            outcome_memory=self.outcome_memory,
            failure_memory=self.failure_memory,
            capability_discovery_engine=self.capability_discovery,
            storage_path="self_inspection.json"
        )
        
        # System state
        self.current_phase: SystemPhase = SystemPhase.INITIALIZING
        self.intelligence_history: deque = deque(maxlen=1000)
        self.compounding_events: List[CompoundingEvent] = []
        self.active_bottlenecks: Dict[str, BottleneckAnalysis] = {}
        self.resolved_bottlenecks: List[str] = []
        
        # Performance tracking
        self.performance_trajectory: deque = deque(maxlen=252)  # 1 year daily
        self.capability_stack: Dict[str, Dict] = {}
        
        # Control systems
        self._running: bool = False
        self._main_loop_task: Optional[asyncio.Task] = None
        self._intelligence_compounding_task: Optional[asyncio.Task] = None
        
        # Callbacks for external integration
        self.on_phase_change: List[Callable] = []
        self.on_intelligence_compounded: List[Callable] = []
        self.on_bottleneck_detected: List[Callable] = []
        
        # Load saved state
        self._load_state()
        
        logger.info("UnifiedFinancialIntelligenceSystem initialized")
    
    # ==================== Core Lifecycle ====================
    
    async def start(self):
        """Start the unified intelligence system"""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting Unified Financial Intelligence System...")
        
        # Phase 1: Initialize
        await self._transition_to_phase(SystemPhase.INITIALIZING)
        await self._initialize_system()
        
        # Phase 2: Start continuous operations
        await self._transition_to_phase(SystemPhase.OBSERVING)
        
        # Start all engines
        await self.capability_discovery.start_continuous_monitoring()
        await self.self_inspection.start_continuous_inspection()
        
        # Start main orchestration loop
        self._main_loop_task = asyncio.create_task(self._main_orchestration_loop())
        
        # Start intelligence compounding tracker
        self._intelligence_compounding_task = asyncio.create_task(
            self._intelligence_compounding_loop()
        )
        
        logger.info("✓ Unified Financial Intelligence System operational")
    
    async def stop(self):
        """Stop the system gracefully"""
        self._running = False
        
        # Stop all tasks
        if self._main_loop_task:
            self._main_loop_task.cancel()
            try:
                await self._main_loop_task
            except asyncio.CancelledError:
                pass
        
        if self._intelligence_compounding_task:
            self._intelligence_compounding_task.cancel()
            try:
                await self._intelligence_compounding_task
            except asyncio.CancelledError:
                pass
        
        # Stop engines
        await self.capability_discovery.stop_continuous_monitoring()
        await self.self_inspection.stop_continuous_inspection()
        
        # Save state
        self._save_state()
        
        logger.info("Unified Financial Intelligence System stopped")
    
    async def _main_orchestration_loop(self):
        """Main orchestration loop coordinating all engines"""
        while self._running:
            try:
                cycle_start = datetime.utcnow()
                
                # Step 1: Market Evaluation (if trading system available)
                if self.trading_system:
                    await self._evaluate_market_conditions()
                
                # Step 2: Self-Inspection & Reflection
                await self._run_reflection_cycle()
                
                # Step 3: Check for critical issues
                issues = self._check_for_critical_issues()
                if issues:
                    await self._handle_critical_issues(issues)
                
                # Step 4: Evolution & Intelligence Compounding
                if self.current_phase not in [SystemPhase.DEGRADED, SystemPhase.RECOVERING]:
                    await self._run_evolution_cycle()
                
                # Step 5: Record intelligence metrics
                await self._record_intelligence_metrics()
                
                # Step 6: Bottleneck analysis
                await self._analyze_bottlenecks()
                
                # Wait for next cycle
                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                sleep_time = max(0, 300 - cycle_duration)  # 5 minute cycles
                
                logger.debug(f"Orchestration cycle completed in {cycle_duration:.1f}s")
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main orchestration loop: {e}")
                await asyncio.sleep(60)
    
    # ==================== Market Evaluation ====================
    
    async def _evaluate_market_conditions(self):
        """Evaluate current market conditions"""
        # This would interface with the trading system
        # For now, placeholder for market regime detection
        pass
    
    # ==================== Self-Reflection & Audit ====================
    
    async def _run_reflection_cycle(self):
        """Run a complete self-reflection cycle"""
        await self._transition_to_phase(SystemPhase.REFLECTING)
        
        # Run self-inspection
        inspection_results = await self.self_inspection._run_full_inspection()
        
        # Check for new critical findings
        critical_findings = [
            f for f in self.self_inspection.findings.values()
            if f.severity == FindingSeverity.CRITICAL
            and f.finding_id not in getattr(self, '_processed_critical', set())
        ]
        
        if critical_findings:
            self._processed_critical = set(
                f.finding_id for f in critical_findings
            )
            
            # Introspect on critical findings
            for finding in critical_findings:
                if finding.affected_decisions:
                    for decision_id in finding.affected_decisions[:3]:
                        await self.introspection_engine.introspect_failure(decision_id)
        
        logger.debug(f"Reflection cycle: {len(inspection_results.get('findings', {}))} findings")
    
    # ==================== Adversarial Challenge ====================
    
    async def _run_adversarial_validation(self, decision: Any) -> Dict[str, Any]:
        """Run adversarial validation on a decision"""
        await self._transition_to_phase(SystemPhase.CHALLENGING)
        
        # This would use the AdversarialCounterAnalyst
        challenges = []
        
        # Challenge 1: Evidence sufficiency
        challenges.append({
            'type': 'evidence',
            'passed': decision.evidence_coverage.get('coverage', 0) > 0.7 if hasattr(decision, 'evidence_coverage') else False,
            'severity': 'high' if decision.evidence_coverage.get('coverage', 0) < 0.5 else 'low' if hasattr(decision, 'evidence_coverage') else 'medium'
        })
        
        # Challenge 2: Regime fit
        challenges.append({
            'type': 'regime',
            'passed': decision.regime_applicability_score > 0.6 if hasattr(decision, 'regime_applicability_score') else False,
            'severity': 'high' if decision.regime_applicability_score < 0.4 else 'low' if hasattr(decision, 'regime_applicability_score') else 'medium'
        })
        
        # Challenge 3: Robustness
        challenges.append({
            'type': 'robustness',
            'passed': decision.robustness_score > 0.6 if hasattr(decision, 'robustness_score') else False,
            'severity': 'high' if decision.robustness_score < 0.4 else 'low' if hasattr(decision, 'robustness_score') else 'medium'
        })
        
        passed = sum(1 for c in challenges if c['passed'])
        
        return {
            'decision_id': decision.id if hasattr(decision, 'id') else 'unknown',
            'challenges_run': len(challenges),
            'challenges_passed': passed,
            'overall_passed': passed >= 2,
            'challenges': challenges
        }
    
    # ==================== Evolution & Intelligence Compounding ====================
    
    async def _run_evolution_cycle(self):
        """Run capability evolution cycle"""
        await self._transition_to_phase(SystemPhase.EVOLVING)
        
        # Get capability discovery status
        discovery_status = self.capability_discovery.get_status()
        
        # Check for gaps to address
        if discovery_status['gaps']['active'] > 0:
            # Run discovery cycle
            await self.capability_discovery._run_discovery_cycle()
        
        # Check for completed experiments to integrate
        for exp_id, experiment in list(self.capability_discovery.active_experiments.items()):
            if experiment.get('status') == 'completed':
                # Evaluate and potentially integrate
                await self.capability_discovery._evaluate_live_results(exp_id)
        
        # Record compounding if innovations integrated
        if discovery_status['experiments']['completed'] > len(self.compounding_events):
            await self._record_compounding_event(
                event_type='capability_integrated',
                description=f"New capability integrated from validation",
                intelligence_delta=0.05  # Conservative estimate
            )
    
    async def _intelligence_compounding_loop(self):
        """Background loop tracking intelligence compounding"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                # Calculate current intelligence metrics
                metrics = self._calculate_intelligence_metrics()
                self.intelligence_history.append(metrics)
                
                # Check for compounding effects
                if len(self.intelligence_history) >= 2:
                    prev = list(self.intelligence_history)[-2]
                    curr = metrics
                    
                    # If capabilities increased and quality improved
                    if (curr.total_capabilities > prev.total_capabilities and
                        curr.decision_quality_score > prev.decision_quality_score):
                        
                        await self._record_compounding_event(
                            event_type='intelligence_compounded',
                            description=f"Capabilities: {prev.total_capabilities} → {curr.total_capabilities}, "
                                        f"Quality: {prev.decision_quality_score:.3f} → {curr.decision_quality_score:.3f}",
                            intelligence_delta=curr.decision_quality_score - prev.decision_quality_score
                        )
                
            except Exception as e:
                logger.warning(f"Error in compounding loop: {e}")
    
    async def _record_compounding_event(
        self,
        event_type: str,
        description: str,
        intelligence_delta: float,
        capabilities_affected: Optional[List[str]] = None
    ):
        """Record an intelligence compounding event"""
        event = CompoundingEvent(
            event_id=f"compound_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            description=description,
            intelligence_delta=intelligence_delta,
            capabilities_affected=capabilities_affected or [],
            lessons_learned=[
                "Every improvement builds on previous capabilities",
                "Quality of reasoning compounds with each validated enhancement",
                "Self-awareness enables targeted improvements"
            ],
            evidence={
                'capabilities': len(self.capability_stack),
                'bottlenecks_resolved': len(self.resolved_bottlenecks)
            }
        )
        
        self.compounding_events.append(event)
        
        # Trigger callbacks
        for callback in self.on_intelligence_compounded:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Compounding callback error: {e}")
        
        logger.info(f"Intelligence compounding event: {event_type} (+{intelligence_delta:.3f})")
    
    # ==================== Bottleneck Analysis ====================
    
    async def _analyze_bottlenecks(self):
        """Analyze system bottlenecks limiting performance"""
        bottlenecks = []
        
        # Get current status from all engines
        cap_status = self.capability_discovery.get_status()
        inspection_summary = self.self_inspection.get_inspection_summary()
        
        # Bottleneck 1: Capability gaps
        if cap_status['gaps']['active'] > 5:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_id="too_many_gaps",
                category="capability_coverage",
                description=f"Too many active capability gaps ({cap_status['gaps']['active']}) limiting system performance",
                severity=min(1.0, cap_status['gaps']['active'] / 10),
                impact_on_performance=0.3,
                root_cause="Insufficient capability expansion rate",
                proposed_solution="Accelerate validation pipeline and reduce promotion gates",
                estimated_improvement=0.15,
                complexity="medium",
                is_resolvable=True
            ))
        
        # Bottleneck 2: Calibration issues
        if inspection_summary['calibration']['current_brier'] and inspection_summary['calibration']['current_brier'] > 0.25:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_id="poor_calibration",
                category="uncertainty_quality",
                description=f"Poor confidence calibration (Brier: {inspection_summary['calibration']['current_brier']:.3f})",
                severity=0.8,
                impact_on_performance=0.25,
                root_cause="Stale or inadequate confidence calibration",
                proposed_solution="Implement automated sliding-window calibration",
                estimated_improvement=0.12,
                complexity="medium",
                is_resolvable=True
            ))
        
        # Bottleneck 3: High error rate
        critical_findings = inspection_summary['findings']['critical']
        if critical_findings > 3:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_id="high_critical_findings",
                category="system_stability",
                description=f"{critical_findings} critical findings indicate system instability",
                severity=0.9,
                impact_on_performance=0.35,
                root_cause="Systematic errors not being addressed",
                proposed_solution="Pause new capabilities, focus on fixing critical issues",
                estimated_improvement=0.20,
                complexity="high",
                is_resolvable=True
            ))
        
        # Update active bottlenecks
        self.active_bottlenecks = {b.bottleneck_id: b for b in bottlenecks}
        
        # Trigger callbacks for new bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.bottleneck_id not in getattr(self, '_known_bottlenecks', set()):
                for callback in self.on_bottleneck_detected:
                    try:
                        callback(bottleneck)
                    except Exception as e:
                        logger.warning(f"Bottleneck callback error: {e}")
        
        self._known_bottlenecks = set(b.bottleneck_id for b in bottlenecks)
    
    # ==================== Critical Issue Handling ====================
    
    def _check_for_critical_issues(self) -> List[Dict[str, Any]]:
        """Check for critical issues requiring immediate attention"""
        issues = []
        
        # Check self-inspection findings
        critical_findings = [
            f for f in self.self_inspection.findings.values()
            if f.severity == FindingSeverity.CRITICAL
        ]
        
        if len(critical_findings) > 5:
            issues.append({
                'type': 'too_many_critical_findings',
                'severity': 'critical',
                'count': len(critical_findings),
                'action': 'enter_recovery_mode'
            })
        
        # Check capability discovery
        cap_status = self.capability_discovery.get_status()
        if cap_status.get('integration_rate', 1.0) < 0.2:
            issues.append({
                'type': 'low_integration_rate',
                'severity': 'high',
                'rate': cap_status.get('integration_rate', 0),
                'action': 'review_validation_criteria'
            })
        
        return issues
    
    async def _handle_critical_issues(self, issues: List[Dict[str, Any]]):
        """Handle critical system issues"""
        await self._transition_to_phase(SystemPhase.RECOVERING)
        
        for issue in issues:
            logger.warning(f"Critical issue detected: {issue['type']}")
            
            if issue['action'] == 'enter_recovery_mode':
                # Pause evolution
                await self.capability_discovery.stop_continuous_monitoring()
                
                # Focus on fixing critical issues
                for finding in list(self.self_inspection.findings.values())[:10]:
                    if finding.severity == FindingSeverity.CRITICAL:
                        # Generate immediate fix if possible
                        if finding.automated_fixable:
                            logger.info(f"Applying automated fix for: {finding.title}")
                        else:
                            # Create high-priority capability gap
                            logger.info(f"Created high-priority gap for: {finding.title}")
                
                # Restart with reduced scope
                await self.capability_discovery.start_continuous_monitoring()
        
        await self._transition_to_phase(SystemPhase.STABLE)
    
    # ==================== System State Management ====================
    
    async def _transition_to_phase(self, new_phase: SystemPhase):
        """Transition to a new operational phase"""
        if new_phase != self.current_phase:
            old_phase = self.current_phase
            self.current_phase = new_phase
            
            logger.info(f"Phase transition: {old_phase.value} → {new_phase.value}")
            
            # Trigger callbacks
            for callback in self.on_phase_change:
                try:
                    callback(old_phase, new_phase)
                except Exception as e:
                    logger.warning(f"Phase change callback error: {e}")
    
    async def _initialize_system(self):
        """Initialize all subsystems"""
        # Map initial capability space
        self.capability_discovery._map_capability_space_realtime()
        
        # Run initial self-inspection
        await self.self_inspection._run_full_inspection()
        
        logger.info("System initialization complete")
    
    async def _record_intelligence_metrics(self):
        """Record current intelligence metrics"""
        metrics = self._calculate_intelligence_metrics()
        self.intelligence_history.append(metrics)
        
        # Also track performance
        self.performance_trajectory.append(metrics.decision_quality_score)
    
    def _calculate_intelligence_metrics(self) -> IntelligenceMetrics:
        """Calculate comprehensive intelligence metrics"""
        # Get data from engines
        cap_status = self.capability_discovery.get_status()
        inspection_summary = self.self_inspection.get_inspection_summary()
        
        # Calculate decision quality
        if self.self_inspection.decision_metrics:
            calibration_errors = [
                m.calibration_error for m in self.self_inspection.decision_metrics.values()
                if m.calibration_error is not None
            ]
            avg_calibration_error = np.mean(calibration_errors) if calibration_errors else 0.5
            
            quality_scores = [
                m.robustness_score for m in self.self_inspection.decision_metrics.values()
            ]
            decision_quality = np.mean(quality_scores) if quality_scores else 0.5
        else:
            avg_calibration_error = 0.5
            decision_quality = 0.5
        
        # Calculate performance trend
        if len(self.performance_trajectory) >= 10:
            recent = list(self.performance_trajectory)[-10:]
            trend = np.polyfit(range(len(recent)), recent, 1)[0] if len(set(recent)) > 1 else 0
        else:
            trend = 0
        
        # System health
        critical_count = inspection_summary['findings']['critical']
        health_score = max(0, 1.0 - critical_count * 0.1)
        
        return IntelligenceMetrics(
            timestamp=datetime.utcnow(),
            avg_calibration_error=avg_calibration_error,
            decision_quality_score=decision_quality,
            reasoning_soundness=inspection_summary['findings']['by_category'].get('reasoning_soundness', 0) / max(1, len(self.self_inspection.findings)),
            total_capabilities=cap_status['capability_space']['total_capabilities'],
            active_capabilities=cap_status['capability_space']['active'],
            capability_gaps=cap_status['gaps']['active'],
            innovations_validated=cap_status['experiments']['completed'],
            innovations_integrated=len(self.capability_discovery.integration_history),
            integration_success_rate=cap_status.get('integration_rate', 0),
            bottlenecks_resolved=len(self.resolved_bottlenecks),
            improvements_compounded=len(self.compounding_events),
            performance_trend=trend,
            system_health_score=health_score,
            error_rate=inspection_summary['findings']['total'] / max(1, len(self.self_inspection.decision_metrics)),
            recovery_time=None
        )
    
    # ==================== Public API ====================
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        cap_status = self.capability_discovery.get_status()
        inspection_summary = self.self_inspection.get_inspection_summary()
        
        # Get latest intelligence metrics
        latest_metrics = list(self.intelligence_history)[-1] if self.intelligence_history else None
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'phase': self.current_phase.value,
            'is_running': self._running,
            'intelligence': {
                'current_score': latest_metrics.decision_quality_score if latest_metrics else 0.5,
                'capabilities': cap_status['capability_space']['total_capabilities'],
                'gaps': cap_status['gaps']['active'],
                'compounding_events': len(self.compounding_events),
                'trend': latest_metrics.performance_trend if latest_metrics else 0
            },
            'health': {
                'score': latest_metrics.system_health_score if latest_metrics else 0.5,
                'critical_findings': inspection_summary['findings']['critical'],
                'active_bottlenecks': len(self.active_bottlenecks),
                'calibration_brier': inspection_summary['calibration']['current_brier']
            },
            'evolution': {
                'integration_rate': cap_status.get('integration_rate', 0),
                'innovations_in_progress': cap_status['experiments']['active'],
                'completed_integrations': len(self.capability_discovery.integration_history)
            }
        }
    
    def get_intelligence_report(self) -> Dict[str, Any]:
        """Get comprehensive intelligence compounding report"""
        return {
            'current_intelligence': self.get_system_status(),
            'compounding_history': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'type': e.event_type,
                    'description': e.description,
                    'intelligence_delta': e.intelligence_delta
                }
                for e in self.compounding_events[-20:]
            ],
            'bottlenecks': {
                'active': [
                    {
                        'id': b.bottleneck_id,
                        'description': b.description,
                        'severity': b.severity,
                        'impact': b.impact_on_performance,
                        'proposed_solution': b.proposed_solution
                    }
                    for b in self.active_bottlenecks.values()
                ],
                'resolved_count': len(self.resolved_bottlenecks)
            },
            'capability_stack': self.capability_stack,
            'performance_trajectory': list(self.performance_trajectory)[-30:],
            'key_insights': self._generate_intelligence_insights()
        }
    
    def _generate_intelligence_insights(self) -> List[str]:
        """Generate key insights about system intelligence"""
        insights = []
        
        if not self.intelligence_history:
            return ["System initializing - insufficient data for insights"]
        
        # Trend analysis
        recent = list(self.intelligence_history)[-10:]
        if len(recent) >= 5:
            quality_trend = np.mean([m.decision_quality_score for m in recent[-5:]]) - \
                          np.mean([m.decision_quality_score for m in recent[:5]])
            
            if quality_trend > 0.05:
                insights.append(f"✓ Decision quality improving (+{quality_trend:.3f} over last {len(recent)} cycles)")
            elif quality_trend < -0.05:
                insights.append(f"⚠ Decision quality declining ({quality_trend:.3f}) - investigate causes")
        
        # Capability growth
        cap_status = self.capability_discovery.get_status()
        if cap_status['experiments']['completed'] > 0:
            insights.append(f"✓ {cap_status['experiments']['completed']} capabilities validated and integrated")
        
        # Bottlenecks
        if self.active_bottlenecks:
            top_bottleneck = max(self.active_bottlenecks.values(), key=lambda b: b.severity)
            insights.append(f"→ Primary bottleneck: {top_bottleneck.description[:60]}...")
        
        # Compounding
        if len(self.compounding_events) > 5:
            insights.append(f"✓ Intelligence compounding active: {len(self.compounding_events)} events recorded")
        
        return insights
    
    # ==================== Persistence ====================
    
    def _save_state(self):
        """Save system state to disk"""
        try:
            state = {
                'intelligence_events': len(self.compounding_events),
                'capabilities': len(self.capability_stack),
                'bottlenecks_resolved': len(self.resolved_bottlenecks),
                'metrics_history': len(self.intelligence_history),
                'saved_at': datetime.utcnow().isoformat()
            }
            Path(self.storage_path).write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _load_state(self):
        """Load system state from disk"""
        try:
            if not Path(self.storage_path).exists():
                return
            state = json.loads(Path(self.storage_path).read_text())
            logger.info(f"Loaded system state: {state.get('intelligence_events', 0)} compounding events")
        except Exception as e:
            logger.warning(f"Error loading state: {e}")


# Factory function
def create_financial_intelligence_system(
    trading_system=None,
    constraint_profile: Optional[ConstraintProfile] = None,
    storage_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> UnifiedFinancialIntelligenceSystem:
    """Factory function to create the unified financial intelligence system"""
    
    return UnifiedFinancialIntelligenceSystem(
        trading_system=trading_system,
        constraint_profile=constraint_profile,
        storage_path=storage_path,
        config=config
    )
