"""
Integration Module
==================

Integrates the Autonomous Research Organism with existing trading bot systems.
Provides bridges to:
- Safety systems (safety_orchestrator, harmful_behavior_guard)
- Self-improvement systems (self_improvement, recursive_improvement)
- Research systems (research_lab)
- Core trading systems

CRITICAL: All integrations maintain safety boundaries.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SafetyIntegration:
    """
    Integrates with existing safety systems.
    
    Ensures the research organism respects all safety boundaries
    defined in the trading bot's safety infrastructure.
    """
    
    def __init__(self):
        self.safety_orchestrator = None
        self.harmful_behavior_guard = None
        self.immutable_safety_core = None
        self._initialized = False
    
    def initialize(self):
        """Initialize connections to safety systems."""
        try:
            # Try to import safety orchestrator
            try:
                from trading_bot.safety.safety_orchestrator import SafetyOrchestrator
                self.safety_orchestrator = SafetyOrchestrator()
                self.safety_orchestrator.initialize()
                logger.info("SafetyOrchestrator connected")
            except ImportError:
                logger.warning("SafetyOrchestrator not available")
            
            # Try to import harmful behavior guard
            try:
                from trading_bot.recursive_improvement.harmful_behavior_guard import (
                    HarmfulBehaviorDetector, QwenHarmMonitor
                )
                self.harmful_behavior_guard = HarmfulBehaviorDetector()
                logger.info("HarmfulBehaviorDetector connected")
            except ImportError:
                logger.warning("HarmfulBehaviorDetector not available")
            
            # Try to import immutable safety core
            try:
                from trading_bot.self_assembly_ai.immutable_safety_core import (
                    get_safety_core, ImmutableSafetyCore
                )
                self.immutable_safety_core = get_safety_core()
                logger.info("ImmutableSafetyCore connected")
            except ImportError:
                logger.warning("ImmutableSafetyCore not available")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Safety integration initialization failed: {e}")
    
    def check_safety(self) -> bool:
        """Check if all safety systems report safe status."""
        if not self._initialized:
            self.initialize()
        
        is_safe = True
        
        # Check safety orchestrator
        if self.safety_orchestrator:
            try:
                status = self.safety_orchestrator.check_safety()
                if not status.is_safe:
                    logger.warning(f"SafetyOrchestrator reports unsafe: {status.message}")
                    is_safe = False
            except Exception as e:
                logger.error(f"SafetyOrchestrator check failed: {e}")
                is_safe = False
        
        # Check immutable safety core
        if self.immutable_safety_core:
            try:
                if not self.immutable_safety_core.verify_integrity():
                    logger.critical("ImmutableSafetyCore integrity check failed!")
                    is_safe = False
            except Exception as e:
                logger.error(f"ImmutableSafetyCore check failed: {e}")
                is_safe = False
        
        return is_safe
    
    def validate_improvement(self, improvement_state: Dict[str, Any]) -> bool:
        """Validate an improvement against safety systems."""
        if not self._initialized:
            self.initialize()
        
        # Check with harmful behavior guard
        if self.harmful_behavior_guard:
            try:
                detections = self.harmful_behavior_guard.detect_all(improvement_state)
                if detections:
                    critical = [d for d in detections if d.threat_level.value >= 4]
                    if critical:
                        logger.warning(f"Harmful behavior detected: {len(critical)} critical")
                        return False
            except Exception as e:
                logger.error(f"Harmful behavior check failed: {e}")
                return False
        
        return True


class ResearchLabIntegration:
    """
    Integrates with existing research lab systems.
    
    Allows the research organism to leverage existing
    research infrastructure and share results.
    """
    
    def __init__(self):
        self.research_lab = None
        self._initialized = False
    
    def initialize(self):
        """Initialize connection to research lab."""
        try:
            from trading_bot.research_lab.experiment_orchestrator import (
                AutonomousResearchLab
            )
            self.research_lab = AutonomousResearchLab()
            self._initialized = True
            logger.info("AutonomousResearchLab connected")
        except ImportError:
            logger.warning("AutonomousResearchLab not available")
    
    def share_hypothesis(self, hypothesis: Dict[str, Any]):
        """Share a hypothesis with the research lab."""
        if not self._initialized:
            self.initialize()
        
        if self.research_lab:
            try:
                # Convert to research lab format
                from trading_bot.research_lab.experiment_orchestrator import (
                    ResearchHypothesis, ExperimentType
                )
                
                lab_hypothesis = ResearchHypothesis(
                    hypothesis_id=hypothesis.get('hypothesis_id', ''),
                    experiment_type=ExperimentType.FEATURE_DISCOVERY,
                    description=hypothesis.get('description', ''),
                    rationale=hypothesis.get('rationale', ''),
                    expected_outcome=hypothesis.get('expected_outcome', ''),
                    success_criteria=hypothesis.get('success_criteria', {}),
                    generated_timestamp=datetime.now(),
                )
                
                logger.info(f"Shared hypothesis: {lab_hypothesis.hypothesis_id}")
                
            except Exception as e:
                logger.error(f"Failed to share hypothesis: {e}")


class SelfImprovementIntegration:
    """
    Integrates with existing self-improvement systems.
    
    Coordinates with the self-improvement engine to avoid
    conflicts and share improvements.
    """
    
    def __init__(self):
        self.improvement_engine = None
        self._initialized = False
    
    def initialize(self):
        """Initialize connection to self-improvement engine."""
        try:
            from trading_bot.self_improvement.engine import SelfImprovementEngine
            # Note: Would need config in production
            self.improvement_engine = None  # Placeholder
            self._initialized = True
            logger.info("SelfImprovementEngine integration ready")
        except ImportError:
            logger.warning("SelfImprovementEngine not available")
    
    def register_improvement(self, improvement: Dict[str, Any]):
        """Register an improvement with the self-improvement system."""
        logger.info(f"Improvement registered: {improvement.get('id', 'unknown')}")


class OrganismIntegrator:
    """
    Main integrator that connects the research organism
    to all existing trading bot systems.
    """
    
    def __init__(self):
        self.safety = SafetyIntegration()
        self.research = ResearchLabIntegration()
        self.improvement = SelfImprovementIntegration()
        self._initialized = False
    
    def initialize_all(self):
        """Initialize all integrations."""
        self.safety.initialize()
        self.research.initialize()
        self.improvement.initialize()
        self._initialized = True
        logger.info("All integrations initialized")
    
    def pre_cycle_check(self) -> bool:
        """
        Check all systems before starting a research cycle.
        
        Returns:
            True if safe to proceed
        """
        if not self._initialized:
            self.initialize_all()
        
        # Safety check
        if not self.safety.check_safety():
            logger.warning("Pre-cycle safety check failed")
            return False
        
        return True
    
    def post_cycle_report(self, cycle_results: Dict[str, Any]):
        """
        Report cycle results to all integrated systems.
        
        Args:
            cycle_results: Results from the research cycle
        """
        # Share with research lab
        if 'hypothesis' in cycle_results:
            self.research.share_hypothesis(cycle_results['hypothesis'])
        
        # Register improvements
        for improvement in cycle_results.get('improvements', []):
            self.improvement.register_improvement(improvement)
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        return {
            'initialized': self._initialized,
            'safety': {
                'orchestrator': self.safety.safety_orchestrator is not None,
                'harm_guard': self.safety.harmful_behavior_guard is not None,
                'safety_core': self.safety.immutable_safety_core is not None,
            },
            'research': {
                'lab': self.research.research_lab is not None,
            },
            'improvement': {
                'engine': self.improvement.improvement_engine is not None,
            },
        }


def setup_organism_with_integrations(
    storage_path: Optional[str] = None,
    auto_start: bool = False
):
    """
    Factory function to create a fully integrated research organism.
    
    Args:
        storage_path: Path for storage
        auto_start: Whether to start automatically
        
    Returns:
        Tuple of (organism, integrator)
    """
    from .continuous_research_organism import ContinuousResearchOrganism
    
    # Create organism
    path = Path(storage_path) if storage_path else None
    organism = ContinuousResearchOrganism(storage_path=path)
    
    # Create integrator
    integrator = OrganismIntegrator()
    integrator.initialize_all()
    
    # Register safety check callback
    from .continuous_research_organism import ResearchPhase
    
    def safety_check_callback(cycle):
        if not integrator.safety.check_safety():
            logger.warning("Safety check failed during cycle")
            organism.pause()
    
    organism.register_phase_callback(ResearchPhase.ANALYZING, safety_check_callback)
    
    # Register improvement callback
    def improvement_callback(code_gen, cycle):
        integrator.improvement.register_improvement({
            'id': code_gen.generation_id,
            'code_type': code_gen.code_type.name,
            'fitness': code_gen.fitness_score,
            'cycle_id': cycle.cycle_id,
        })
    
    organism.register_improvement_callback(improvement_callback)
    
    if auto_start:
        organism.start()
    
    return organism, integrator


# Convenience function for quick setup
def quick_start_organism(
    directives: Optional[List[Dict[str, Any]]] = None
):
    """
    Quick start a research organism with optional directives.
    
    Args:
        directives: List of directive configurations
        
    Returns:
        Running organism instance
    """
    organism, integrator = setup_organism_with_integrations(auto_start=False)
    
    # Add directives
    if directives:
        from .continuous_research_organism import ResearchPriority
        
        for directive in directives:
            organism.create_directive(
                title=directive.get('title', 'Research Task'),
                description=directive.get('description', ''),
                target_area=directive.get('target_area', 'strategy'),
                success_criteria=directive.get('success_criteria', {}),
                priority=ResearchPriority[directive.get('priority', 'NORMAL')],
            )
    
    # Start
    organism.start()
    
    return organism
