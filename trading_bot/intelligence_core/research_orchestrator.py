"""
Research Orchestrator
======================

Master coordinator for the Self-Auditing Quant Research Lab.

ARCHITECTURE:
This is the highest-level design - a self-evaluating, risk-aware learning system
that improves HYPOTHESIS quality (not model quality) while detecting unseen
failure modes.

WHAT IT CAN DO:
✅ Try new features
✅ Tune hyperparameters
✅ Test architectures
✅ Compare strategies
✅ Generate hypotheses
✅ Detect failure modes
✅ Learn from mistakes structurally

WHAT IT CANNOT DO:
❌ Deploy models to production
❌ Change risk rules
❌ Access capital
❌ Modify governance constraints
❌ Execute real trades

CORE PRINCIPLES:
1. AI improves HYPOTHESES, not models
2. AI remembers mistakes STRUCTURALLY, not statistically
3. AI learns how decision-making BREAKS under uncertainty
4. AI becomes HARDER TO FOOL than the market itself
"""

import logging
import threading
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .hypothesis_engine import (
    HypothesisEngine,
    Hypothesis,
    HypothesisStatus,
    HypothesisType,
    TestablePredicition,
    BoundaryCondition
)
from .structural_memory import (
    StructuralMemory,
    FailureMemory,
    FailureCategory,
    FailureSeverity
)
from .failure_detector import (
    FailureModeDetector,
    FailureModeDetection,
    FailureModeType,
    DetectionSeverity
)
from .self_audit import (
    SelfAuditSystem,
    AuditResult,
    AuditStatus
)
from .adversarial_hardening import (
    AdversarialHardening,
    StressTestResult,
    ScenarioType,
    StressLevel,
    RobustnessLevel
)
from .governance import (
    GovernanceLayer,
    CapabilityType,
    ApprovalRequest
)

logger = logging.getLogger(__name__)


class ResearchPhase(Enum):
    """Phases of research"""
    OBSERVATION = "observation"       # Observing market
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    FAILURE_ANALYSIS = "failure_analysis"
    HARDENING = "hardening"
    PROPOSAL = "proposal"             # Proposing to human
    WAITING_APPROVAL = "waiting_approval"
    IDLE = "idle"


@dataclass
class ResearchSession:
    """A research session"""
    session_id: str
    started_at: datetime
    phase: ResearchPhase
    
    # Progress
    hypotheses_generated: int = 0
    hypotheses_tested: int = 0
    hypotheses_killed: int = 0
    hypotheses_graduated: int = 0
    
    # Failures
    failures_recorded: int = 0
    failures_analyzed: int = 0
    
    # Hardening
    stress_tests_run: int = 0
    survival_rate: float = 0.0
    
    # Audits
    audits_run: int = 0
    audit_pass_rate: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'started_at': self.started_at.isoformat(),
            'phase': self.phase.value,
            'hypotheses_generated': self.hypotheses_generated,
            'hypotheses_tested': self.hypotheses_tested,
            'hypotheses_killed': self.hypotheses_killed,
            'hypotheses_graduated': self.hypotheses_graduated,
            'failures_recorded': self.failures_recorded,
            'failures_analyzed': self.failures_analyzed,
            'stress_tests_run': self.stress_tests_run,
            'survival_rate': self.survival_rate,
            'audits_run': self.audits_run,
            'audit_pass_rate': self.audit_pass_rate
        }


@dataclass
class ResearchProposal:
    """A proposal for human review"""
    proposal_id: str
    proposal_type: str
    title: str
    description: str
    
    # Content
    hypotheses: List[Dict] = field(default_factory=list)
    strategies: List[Dict] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)
    
    # Evidence
    test_results: List[Dict] = field(default_factory=list)
    audit_results: List[Dict] = field(default_factory=list)
    stress_test_results: List[Dict] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # Status
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    approved_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'proposal_type': self.proposal_type,
            'title': self.title,
            'description': self.description,
            'hypotheses': self.hypotheses,
            'strategies': self.strategies,
            'findings': self.findings,
            'test_results': self.test_results,
            'audit_results': self.audit_results,
            'stress_test_results': self.stress_test_results,
            'recommendations': self.recommendations,
            'risks': self.risks,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'approved_by': self.approved_by
        }


class ResearchOrchestrator:
    """
    Master orchestrator for the Intelligence Core.
    
    THE HIGHEST-LEVEL DESIGN:
    A self-evaluating, risk-aware learning system that improves
    HYPOTHESIS quality while detecting unseen failure modes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Initialize subsystems
        self.hypothesis_engine = HypothesisEngine(config)
        self.structural_memory = StructuralMemory(config)
        self.failure_detector = FailureModeDetector(config)
        self.self_audit = SelfAuditSystem(config)
        self.adversarial_hardening = AdversarialHardening(config)
        self.governance = GovernanceLayer(config)
        
        # Session tracking
        self.current_session: Optional[ResearchSession] = None
        self.session_history: List[ResearchSession] = []
        
        # Proposals
        self.proposals: Dict[str, ResearchProposal] = {}
        
        # Callbacks
        self.on_failure_detected: List[Callable] = []
        self.on_hypothesis_graduated: List[Callable] = []
        
        # Register failure detection callback
        self.failure_detector.on_detection(self._handle_failure_detection)
        
        logger.info("ResearchOrchestrator initialized - Intelligence Core ready")
    
    def start_session(self) -> ResearchSession:
        """Start a new research session"""
        with self.lock:
            import hashlib
            session_id = hashlib.md5(
                f"session_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            self.current_session = ResearchSession(
                session_id=session_id,
                started_at=datetime.now(),
                phase=ResearchPhase.IDLE
            )
            
            logger.info("Started research session: %s", session_id)
            return self.current_session
    
    def end_session(self) -> ResearchSession:
        """End current research session"""
        with self.lock:
            if self.current_session:
                self.session_history.append(self.current_session)
                session = self.current_session
                self.current_session = None
                logger.info("Ended research session: %s", session.session_id)
                return session
            return None
    
    # =========================================================================
    # HYPOTHESIS MANAGEMENT
    # =========================================================================
    
    def generate_hypotheses(
        self,
        observations: Dict[str, Any]
    ) -> List[Hypothesis]:
        """
        Generate hypotheses from observations.
        
        AI CAN: Generate hypotheses
        AI CANNOT: Deploy them
        """
        with self.lock:
            # Check governance
            allowed, reason = self.governance.check_capability(
                CapabilityType.GENERATE_HYPOTHESES,
                {'observations': observations}
            )
            
            if not allowed:
                logger.warning("Hypothesis generation blocked: %s", reason)
                return []
            
            # Update phase
            if self.current_session:
                self.current_session.phase = ResearchPhase.HYPOTHESIS_GENERATION
            
            # Generate hypotheses
            hypotheses = self.hypothesis_engine.generate_hypotheses(observations)
            
            # Update session
            if self.current_session:
                self.current_session.hypotheses_generated += len(hypotheses)
            
            logger.info("Generated %d hypotheses", len(hypotheses))
            return hypotheses
    
    def test_hypothesis(
        self,
        hypothesis_id: str,
        test_data: Dict[str, Any]
    ) -> Tuple[bool, str, AuditResult]:
        """
        Test a hypothesis with full audit.
        
        Returns:
            Tuple of (passed, reason, audit_result)
        """
        with self.lock:
            # Check governance
            allowed, reason = self.governance.check_capability(
                CapabilityType.RUN_BACKTESTS,
                {'hypothesis_id': hypothesis_id}
            )
            
            if not allowed:
                logger.warning("Hypothesis testing blocked: %s", reason)
                return False, reason, None
            
            # Update phase
            if self.current_session:
                self.current_session.phase = ResearchPhase.HYPOTHESIS_TESTING
            
            # Get hypothesis
            hypothesis = self.hypothesis_engine.get_hypothesis(hypothesis_id)
            if not hypothesis:
                return False, "Hypothesis not found", None
            
            # Audit the hypothesis first
            audit_result = self.self_audit.audit_hypothesis(hypothesis.to_dict())
            
            if audit_result.status == AuditStatus.FAILED:
                logger.warning(
                    "Hypothesis %s failed audit: %s",
                    hypothesis_id,
                    [f.description for f in audit_result.findings]
                )
                return False, "Failed audit", audit_result
            
            # Test hypothesis
            passed, test_reason = self.hypothesis_engine.test_hypothesis(
                hypothesis_id, test_data
            )
            
            # Update session
            if self.current_session:
                self.current_session.hypotheses_tested += 1
                if not passed:
                    self.current_session.hypotheses_killed += 1
                self.current_session.audits_run += 1
            
            return passed, test_reason, audit_result
    
    def graduate_hypothesis(
        self,
        hypothesis_id: str,
        approved_by: str
    ) -> bool:
        """
        Graduate hypothesis (REQUIRES HUMAN APPROVAL).
        
        AI CANNOT: Graduate without human approval
        """
        with self.lock:
            # This requires human approval
            success = self.hypothesis_engine.graduate_hypothesis(
                hypothesis_id, approved_by
            )
            
            if success:
                if self.current_session:
                    self.current_session.hypotheses_graduated += 1
                
                # Notify callbacks
                hypothesis = self.hypothesis_engine.get_hypothesis(hypothesis_id)
                for callback in self.on_hypothesis_graduated:
                    try:
                        callback(hypothesis)
                    except Exception as e:
                        logger.error("Callback failed: %s", e)
            
            return success
    
    # =========================================================================
    # FAILURE MANAGEMENT
    # =========================================================================
    
    def record_failure(
        self,
        description: str,
        category: FailureCategory,
        severity: FailureSeverity,
        market_conditions: Dict[str, Any],
        strategy_state: Dict[str, Any],
        position_state: Dict[str, Any],
        loss_amount: float = 0.0,
        loss_percentage: float = 0.0
    ) -> str:
        """
        Record a failure in structural memory.
        
        AI remembers mistakes STRUCTURALLY, not statistically.
        """
        with self.lock:
            # Update phase
            if self.current_session:
                self.current_session.phase = ResearchPhase.FAILURE_ANALYSIS
            
            # Record failure
            memory_id = self.structural_memory.record_failure(
                description=description,
                category=category,
                severity=severity,
                market_conditions=market_conditions,
                strategy_state=strategy_state,
                position_state=position_state,
                loss_amount=loss_amount,
                loss_percentage=loss_percentage
            )
            
            # Update session
            if self.current_session:
                self.current_session.failures_recorded += 1
            
            return memory_id
    
    def analyze_failure(self, memory_id: str) -> Optional[FailureMemory]:
        """
        Analyze a failure structurally.
        
        Builds causal graphs, matches patterns, generates lessons.
        """
        with self.lock:
            memory = self.structural_memory.analyze_failure(memory_id)
            
            if memory and self.current_session:
                self.current_session.failures_analyzed += 1
            
            return memory
    
    def update_failure_detection(
        self,
        current_state: Dict[str, Any]
    ) -> List[FailureModeDetection]:
        """
        Update failure detection with current state.
        
        Detects failure modes FASTER than the market changes.
        """
        return self.failure_detector.update(current_state)
    
    def _handle_failure_detection(self, detection: FailureModeDetection):
        """Handle failure detection"""
        # Notify callbacks
        for callback in self.on_failure_detected:
            try:
                callback(detection)
            except Exception as e:
                logger.error("Failure detection callback failed: %s", e)
        
        # If critical, record in structural memory
        if detection.severity in [DetectionSeverity.CRITICAL, DetectionSeverity.EMERGENCY]:
            self.record_failure(
                description=detection.description,
                category=FailureCategory.UNKNOWN,
                severity=FailureSeverity.SEVERE if detection.severity == DetectionSeverity.CRITICAL else FailureSeverity.CATASTROPHIC,
                market_conditions=detection.metrics,
                strategy_state={},
                position_state={}
            )
    
    # =========================================================================
    # ADVERSARIAL HARDENING
    # =========================================================================
    
    def harden_strategy(
        self,
        strategy: Dict[str, Any],
        stress_levels: Optional[List[StressLevel]] = None
    ) -> Dict[str, Any]:
        """
        Harden a strategy through adversarial testing.
        
        Become HARDER TO FOOL than the market itself.
        """
        with self.lock:
            # Check governance
            allowed, reason = self.governance.check_capability(
                CapabilityType.TEST_ARCHITECTURES,
                {'strategy': strategy}
            )
            
            if not allowed:
                logger.warning("Strategy hardening blocked: %s", reason)
                return {'error': reason}
            
            # Update phase
            if self.current_session:
                self.current_session.phase = ResearchPhase.HARDENING
            
            # Run hardening
            report = self.adversarial_hardening.harden_strategy(
                strategy, stress_levels
            )
            
            # Update session
            if self.current_session:
                self.current_session.stress_tests_run += report.get('tests_run', 0)
                self.current_session.survival_rate = report.get('survival_rate', 0)
            
            return report
    
    def quick_stress_test(
        self,
        strategy: Dict[str, Any],
        scenario_type: ScenarioType,
        stress_level: StressLevel = StressLevel.MODERATE
    ) -> StressTestResult:
        """Run a quick stress test"""
        return self.adversarial_hardening.quick_stress_test(
            strategy, scenario_type, stress_level
        )
    
    # =========================================================================
    # RESEARCH PROPOSALS
    # =========================================================================
    
    def create_proposal(
        self,
        proposal_type: str,
        title: str,
        description: str,
        hypotheses: Optional[List[str]] = None,
        strategies: Optional[List[Dict]] = None
    ) -> ResearchProposal:
        """
        Create a research proposal for human review.
        
        AI CAN: Create proposals
        AI CANNOT: Approve or deploy them
        """
        with self.lock:
            import hashlib
            proposal_id = hashlib.md5(
                f"proposal_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            # Gather hypothesis data
            hypothesis_data = []
            if hypotheses:
                for h_id in hypotheses:
                    h = self.hypothesis_engine.get_hypothesis(h_id)
                    if h:
                        hypothesis_data.append(h.to_dict())
            
            # Create proposal
            proposal = ResearchProposal(
                proposal_id=proposal_id,
                proposal_type=proposal_type,
                title=title,
                description=description,
                hypotheses=hypothesis_data,
                strategies=strategies or []
            )
            
            self.proposals[proposal_id] = proposal
            
            # Update phase
            if self.current_session:
                self.current_session.phase = ResearchPhase.PROPOSAL
            
            # Request governance approval
            self.governance.request_approval(
                capability=CapabilityType.PROPOSE_CHANGES,
                description=f"Research proposal: {title}",
                details={'proposal_id': proposal_id}
            )
            
            logger.info("Created research proposal: %s - %s", proposal_id, title)
            return proposal
    
    def approve_proposal(
        self,
        proposal_id: str,
        approved_by: str
    ) -> bool:
        """
        Approve a proposal (HUMAN ONLY).
        
        AI CANNOT: Approve proposals
        """
        with self.lock:
            if proposal_id not in self.proposals:
                return False
            
            proposal = self.proposals[proposal_id]
            proposal.status = "approved"
            proposal.approved_by = approved_by
            
            logger.info(
                "Proposal %s APPROVED by %s",
                proposal_id,
                approved_by
            )
            
            return True
    
    def get_pending_proposals(self) -> List[ResearchProposal]:
        """Get all pending proposals"""
        with self.lock:
            return [
                p for p in self.proposals.values()
                if p.status == "pending"
            ]
    
    # =========================================================================
    # COMPREHENSIVE RESEARCH CYCLE
    # =========================================================================
    
    async def run_research_cycle(
        self,
        observations: Dict[str, Any],
        test_data: Dict[str, Any],
        strategy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a complete research cycle.
        
        1. Generate hypotheses from observations
        2. Test hypotheses
        3. Detect failure modes
        4. Analyze failures structurally
        5. Harden strategies
        6. Create proposal for human review
        """
        with self.lock:
            # Start session if needed
            if not self.current_session:
                self.start_session()
            
            results = {
                'session_id': self.current_session.session_id,
                'hypotheses': [],
                'test_results': [],
                'failure_detections': [],
                'hardening_report': None,
                'proposal': None
            }
            
            # 1. Generate hypotheses
            self.current_session.phase = ResearchPhase.HYPOTHESIS_GENERATION
            hypotheses = self.generate_hypotheses(observations)
            results['hypotheses'] = [h.to_dict() for h in hypotheses]
            
            # 2. Test hypotheses
            self.current_session.phase = ResearchPhase.HYPOTHESIS_TESTING
            for hypothesis in hypotheses:
                passed, reason, audit = self.test_hypothesis(
                    hypothesis.hypothesis_id, test_data
                )
                results['test_results'].append({
                    'hypothesis_id': hypothesis.hypothesis_id,
                    'passed': passed,
                    'reason': reason,
                    'audit': audit.to_dict() if audit else None
                })
            
            # 3. Detect failure modes
            current_state = {
                **observations,
                'model_accuracy': test_data.get('accuracy', 0.5),
                'prediction_uncertainty': test_data.get('uncertainty', 0.3)
            }
            detections = self.update_failure_detection(current_state)
            results['failure_detections'] = [d.to_dict() for d in detections]
            
            # 4. Analyze any failures
            self.current_session.phase = ResearchPhase.FAILURE_ANALYSIS
            for detection in detections:
                if detection.severity in [DetectionSeverity.CRITICAL, DetectionSeverity.EMERGENCY]:
                    memory_id = self.record_failure(
                        description=detection.description,
                        category=FailureCategory.UNKNOWN,
                        severity=FailureSeverity.SEVERE,
                        market_conditions=detection.metrics,
                        strategy_state={},
                        position_state={}
                    )
                    self.analyze_failure(memory_id)
            
            # 5. Harden strategy if provided
            if strategy:
                self.current_session.phase = ResearchPhase.HARDENING
                hardening_report = self.harden_strategy(strategy)
                results['hardening_report'] = hardening_report
            
            # 6. Create proposal
            self.current_session.phase = ResearchPhase.PROPOSAL
            graduated_hypotheses = [
                h.hypothesis_id for h in hypotheses
                if h.status == HypothesisStatus.VALIDATED
            ]
            
            if graduated_hypotheses or (strategy and results.get('hardening_report')):
                proposal = self.create_proposal(
                    proposal_type="research_cycle",
                    title=f"Research Cycle {self.current_session.session_id}",
                    description="Results from automated research cycle",
                    hypotheses=graduated_hypotheses,
                    strategies=[strategy] if strategy else None
                )
                results['proposal'] = proposal.to_dict()
            
            # Update phase
            self.current_session.phase = ResearchPhase.WAITING_APPROVAL
            
            return results
    
    # =========================================================================
    # STATUS AND STATISTICS
    # =========================================================================
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all systems"""
        with self.lock:
            return {
                'timestamp': datetime.now().isoformat(),
                'current_session': self.current_session.to_dict() if self.current_session else None,
                'hypothesis_engine': self.hypothesis_engine.get_statistics(),
                'structural_memory': self.structural_memory.get_statistics(),
                'failure_detector': self.failure_detector.get_statistics(),
                'self_audit': self.self_audit.get_statistics(),
                'adversarial_hardening': self.adversarial_hardening.get_statistics(),
                'governance': self.governance.get_statistics(),
                'pending_proposals': len(self.get_pending_proposals()),
                'session_count': len(self.session_history)
            }
    
    def get_risk_level(self) -> Tuple[str, float]:
        """Get current risk level"""
        return self.failure_detector.get_risk_level()
    
    def get_hardening_score(self) -> float:
        """Get hardening score"""
        return self.adversarial_hardening.get_hardening_score()


def quick_start(config: Optional[Dict] = None) -> ResearchOrchestrator:
    """
    Quick start the Intelligence Core.
    
    Args:
        config: Optional configuration
        
    Returns:
        ResearchOrchestrator instance
    """
    orchestrator = ResearchOrchestrator(config or {})
    orchestrator.start_session()
    
    logger.info("Intelligence Core ready - Self-Auditing Quant Research Lab online")
    
    return orchestrator
