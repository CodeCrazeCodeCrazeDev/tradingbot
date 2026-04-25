"""
Aletheia Orchestrator - Central Controller for Three-Subagent System

Based on DeepMind's Aletheia paper, this orchestrator coordinates the Generator,
Verifier, and Reviser subagents for autonomous trading strategy research.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ResearchPhase(Enum):
    """Phases of autonomous research process"""
    IDLE = "idle"
    GENERATING = "generating"
    VERIFYING = "verifying"
    REVISING = "revising"
    COMPLETE = "complete"
    FAILED = "failed"


class AutonomyLevel(Enum):
    """Autonomous Mathematics Research Levels (adapted from Aletheia paper)"""
    LEVEL_A = "A"  # Fully autonomous (human only poses questions)
    LEVEL_C = "C"  # Collaborative (human-AI co-authoring)
    LEVEL_H = "H"  # Human-led (AI assists minor portions)


@dataclass
class StrategyHypothesis:
    """Represents a trading strategy hypothesis"""
    hypothesis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    rationale: str = ""
    market_conditions: List[str] = field(default_factory=list)
    entry_rules: List[str] = field(default_factory=list)
    exit_rules: List[str] = field(default_factory=list)
    risk_parameters: Dict[str, Any] = field(default_factory=dict)
    expected_performance: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    verification_status: str = "pending"
    revision_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    generation_trace: List[Dict] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result of strategy verification"""
    hypothesis_id: str = ""
    is_valid: bool = False
    confidence: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    statistical_significance: float = 0.0
    robustness_score: float = 0.0
    verification_method: str = ""
    verified_at: datetime = field(default_factory=datetime.now)


@dataclass
class RevisionAction:
    """Represents a revision action taken by the Reviser"""
    hypothesis_id: str = ""
    revision_type: str = ""  # "rule_modification", "parameter_tuning", "complete_rewrite"
    changes_made: List[str] = field(default_factory=list)
    rationale: str = ""
    improvement_expected: float = 0.0
    previous_version_id: str = ""
    revised_hypothesis: Optional[StrategyHypothesis] = None
    revised_at: datetime = field(default_factory=datetime.now)


class AletheiaOrchestrator:
    """
    Central orchestrator for the Aletheia-inspired autonomous research system.
    
    Coordinates Generator, Verifier, and Reviser subagents in an iterative loop
    until a valid strategy is produced or maximum attempts reached.
    """
    
    def __init__(
        self,
        generator: 'StrategyGenerator',
        verifier: 'StrategyVerifier',
        reviser: 'StrategyReviser',
        max_iterations: int = 5,
        min_confidence_threshold: float = 0.85,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_C
    ):
        self.generator = generator
        self.verifier = verifier
        self.reviser = reviser
        self.max_iterations = max_iterations
        self.min_confidence_threshold = min_confidence_threshold
        self.autonomy_level = autonomy_level
        
        self.active_hypotheses: Dict[str, StrategyHypothesis] = {}
        self.verification_history: List[VerificationResult] = []
        self.revision_history: List[RevisionAction] = []
        self.current_phase: ResearchPhase = ResearchPhase.IDLE
        
        logger.info(f"AletheiaOrchestrator initialized with autonomy level {autonomy_level.value}")
    
    async def research_strategy(
        self,
        research_prompt: str,
        market_context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> StrategyHypothesis:
        """
        Execute full research cycle: Generate → Verify → Revise (iteratively)
        
        Args:
            research_prompt: Natural language description of desired strategy
            market_context: Current market conditions and data
            constraints: Risk limits, asset classes, etc.
            
        Returns:
            Validated StrategyHypothesis or best effort after max iterations
        """
        logger.info(f"Starting strategy research: {research_prompt[:100]}...")
        self.current_phase = ResearchPhase.GENERATING
        
        # Phase 1: Generate initial hypothesis
        hypothesis = await self.generator.generate(
            prompt=research_prompt,
            market_context=market_context,
            constraints=constraints
        )
        
        self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis
        
        # Iterative loop: Verify → Revise until valid or max iterations
        for iteration in range(self.max_iterations):
            logger.info(f"Research iteration {iteration + 1}/{self.max_iterations}")
            
            # Phase 2: Verify hypothesis
            self.current_phase = ResearchPhase.VERIFYING
            verification = await self.verifier.verify(
                hypothesis=hypothesis,
                market_context=market_context
            )
            
            self.verification_history.append(verification)
            
            # Check if verification passed
            if verification.is_valid and verification.confidence >= self.min_confidence_threshold:
                hypothesis.verification_status = "verified"
                hypothesis.confidence_score = verification.confidence
                logger.info(f"Hypothesis {hypothesis.hypothesis_id} verified with confidence {verification.confidence}")
                self.current_phase = ResearchPhase.COMPLETE
                return hypothesis
            
            # Check if we should stop (last iteration)
            if iteration == self.max_iterations - 1:
                logger.warning(f"Max iterations reached. Returning best effort hypothesis.")
                hypothesis.verification_status = "partial"
                hypothesis.confidence_score = verification.confidence
                self.current_phase = ResearchPhase.FAILED
                return hypothesis
            
            # Phase 3: Revise hypothesis
            self.current_phase = ResearchPhase.REVISING
            revision = await self.reviser.revise(
                hypothesis=hypothesis,
                verification_result=verification,
                iteration=iteration
            )
            
            self.revision_history.append(revision)
            
            # Update to revised hypothesis
            if revision.revised_hypothesis:
                hypothesis = revision.revised_hypothesis
                hypothesis.revision_count = iteration + 1
                self.active_hypotheses[hypothesis.hypothesis_id] = hypothesis
                logger.info(f"Hypothesis revised (attempt {hypothesis.revision_count})")
        
        self.current_phase = ResearchPhase.FAILED
        return hypothesis
    
    async def batch_research(
        self,
        research_prompts: List[str],
        market_context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        parallel: bool = True
    ) -> List[StrategyHypothesis]:
        """
        Research multiple strategies in parallel or sequentially
        
        Args:
            research_prompts: List of strategy research prompts
            market_context: Shared market context
            constraints: Shared constraints
            parallel: Whether to run in parallel
            
        Returns:
            List of StrategyHypothesis results
        """
        if parallel:
            tasks = [
                self.research_strategy(prompt, market_context, constraints)
                for prompt in research_prompts
            ]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for prompt in research_prompts:
                result = await self.research_strategy(prompt, market_context, constraints)
                results.append(result)
            return results
    
    def get_research_statistics(self) -> Dict[str, Any]:
        """Get statistics on research performance"""
        total = len(self.verification_history)
        verified = sum(1 for v in self.verification_history if v.is_valid)
        
        return {
            "total_research_cycles": total,
            "successful_verifications": verified,
            "success_rate": verified / total if total > 0 else 0,
            "average_iterations": sum(h.revision_count for h in self.active_hypotheses.values()) / len(self.active_hypotheses) if self.active_hypotheses else 0,
            "current_phase": self.current_phase.value,
            "active_hypotheses": len(self.active_hypotheses),
            "total_revisions": len(self.revision_history),
            "autonomy_level": self.autonomy_level.value
        }
    
    def export_research_report(self, hypothesis_id: Optional[str] = None) -> Dict[str, Any]:
        """Export detailed research report for documentation"""
        if hypothesis_id:
            hypothesis = self.active_hypotheses.get(hypothesis_id)
            if not hypothesis:
                return {"error": "Hypothesis not found"}
            
            return {
                "hypothesis": hypothesis,
                "verifications": [v for v in self.verification_history if v.hypothesis_id == hypothesis_id],
                "revisions": [r for r in self.revision_history if r.hypothesis_id == hypothesis_id],
                "research_trace": hypothesis.generation_trace
            }
        
        # Return all research
        return {
            "hypotheses": list(self.active_hypotheses.values()),
            "verifications": self.verification_history,
            "revisions": self.revision_history,
            "statistics": self.get_research_statistics()
        }
