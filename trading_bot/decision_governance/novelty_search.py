"""
Novelty Search System

Fix #7: Your Meta-Evolution Engine Will Converge on Local Optima

The attack: You promote only changes that "increase robustness, safety, and economic value" 
with "statistical proof." Over time, your system will converge on a set of capabilities 
that are locally optimal given past regimes and past failure patterns.

Fix: Reserve 10-20% of the validation budget for "novelty search"—capabilities that don't 
improve current metrics but expand behavioral repertoire. Maintain a second, non-dominant 
Capability Registry for exploratory innovations.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class CapabilityStatus(Enum):
    """Status of a capability in the registry"""
    EXPLORATORY = "exploratory"      # In novelty search phase
    VALIDATING = "validating"      # Being evaluated
    PROMOTED = "promoted"          # Moved to main registry
    REJECTED = "rejected"          # Failed validation
    DORMANT = "dormant"            # Preserved but not active


@dataclass
class ExploratoryCapability:
    """A capability in the exploratory (non-dominant) registry"""
    capability_id: str
    name: str
    description: str
    created_timestamp: datetime
    
    # Novelty characteristics
    behavioral_difference_score: float  # How different from existing capabilities
    novelty_dimensions: List[str]        # What makes this novel
    inspired_by: Optional[str]           # Parent capability if evolved
    
    # Status
    status: CapabilityStatus = CapabilityStatus.EXPLORATORY
    
    # Validation metrics (different from main registry)
    validation_runs: int = 0
    behavioral_coverage_expansion: float = 0.0  # How much new behavior space it covers
    traditional_performance: Optional[float] = None  # May be worse than existing
    
    # History
    test_results: List[Dict] = field(default_factory=list)
    promotion_evaluations: List[Dict] = field(default_factory=list)
    
    def to_main_registry_format(self) -> Dict:
        """Convert to format suitable for main capability registry"""
        return {
            'id': self.capability_id,
            'name': self.name,
            'description': self.description,
            'behavioral_coverage': self.behavioral_coverage_expansion,
            'validated_at': datetime.utcnow().isoformat()
        }


@dataclass
class NoveltySearchBudget:
    """Budget allocation for novelty search"""
    total_validation_budget_pct: float = 0.15  # 15% default
    exploration_to_validation_ratio: float = 0.7  # 70% exploration, 30% validation
    
    # Absolute limits
    max_exploratory_capabilities: int = 50
    max_concurrent_tests: int = 5
    
    # Promotion criteria (different from main registry)
    min_behavioral_coverage_expansion: float = 0.1  # Must cover 10% new behavior space
    max_traditional_performance_decline: float = 0.3  # Can be 30% worse


class NoveltySearchEngine:
    """
    Novelty Search Engine
    
    Reserves 10-20% of validation budget for exploring capabilities that:
    - Don't necessarily improve current metrics
    - Expand behavioral repertoire
    - May perform worse on traditional measures
    - Cover new areas of decision/action space
    
    Maintains separate "non-dominant" registry for these exploratory capabilities,
    preventing them from being prematurely eliminated by local optimization.
    
    Promotion to main registry happens through:
    1. Demonstrated behavioral coverage expansion
    2. Discovery of novel regime applicability
    3. Combinations with existing capabilities that create emergent value
    """
    
    def __init__(self, budget: Optional[NoveltySearchBudget] = None):
        self.budget = budget or NoveltySearchBudget()
        
        # Non-dominant (exploratory) capability registry
        self.exploratory_registry: Dict[str, ExploratoryCapability] = {}
        
        # Track novelty dimensions explored
        self.behavioral_space_coverage: Set[str] = set()
        self.coverage_history: List[Dict] = []
        
        # Statistics
        self.total_explored: int = 0
        self.promoted_to_main: int = 0
        self.rejected: int = 0
        
        # Current test queue
        self.test_queue: List[str] = []
        
        logger.info(
            f"Novelty Search Engine initialized: "
            f"{self.budget.total_validation_budget_pct:.0%} budget reserved for exploration"
        )
    
    def propose_exploratory_capability(
        self,
        name: str,
        description: str,
        novelty_dimensions: List[str],
        behavioral_difference_score: float,
        inspired_by: Optional[str] = None
    ) -> Optional[ExploratoryCapability]:
        """
        Propose a new exploratory capability.
        
        Unlike main registry proposals, these don't need to show immediate
        performance improvement. They need to demonstrate novelty.
        """
        # Check if we have budget
        if len(self.exploratory_registry) >= self.budget.max_exploratory_capabilities:
            # Evict oldest dormant capability
            self._evict_oldest_dormant()
        
        # Check novelty is sufficient
        if behavioral_difference_score < 0.2:
            logger.info(f"Capability {name} rejected: insufficient novelty")
            return None
        
        capability_id = f"exploratory_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        capability = ExploratoryCapability(
            capability_id=capability_id,
            name=name,
            description=description,
            created_timestamp=datetime.utcnow(),
            behavioral_difference_score=behavioral_difference_score,
            novelty_dimensions=novelty_dimensions,
            inspired_by=inspired_by,
            status=CapabilityStatus.EXPLORATORY
        )
        
        self.exploratory_registry[capability_id] = capability
        self.total_explored += 1
        
        logger.info(
            f"New exploratory capability added: {capability_id} ({name}) "
            f"with novelty score {behavioral_difference_score:.2f}"
        )
        
        return capability
    
    def evaluate_for_promotion(
        self,
        capability_id: str,
        test_results: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Evaluate if an exploratory capability should be promoted to main registry.
        
        Promotion criteria (different from main registry):
        1. Behavioral coverage expansion >= threshold
        2. Does not severely underperform (can be worse, but not catastrophically)
        3. Demonstrates consistent behavior in test regimes
        
        Returns: (should_promote, reason)
        """
        if capability_id not in self.exploratory_registry:
            return False, "capability_not_found"
        
        cap = self.exploratory_registry[capability_id]
        
        # Check behavioral coverage expansion
        coverage_expansion = test_results.get('behavioral_coverage_expansion', 0)
        if coverage_expansion < self.budget.min_behavioral_coverage_expansion:
            cap.status = CapabilityStatus.REJECTED
            self.rejected += 1
            return False, f"insufficient_coverage_expansion ({coverage_expansion:.2f})"
        
        # Check traditional performance (can be worse, but not too bad)
        traditional_perf = test_results.get('traditional_performance', 1.0)
        if traditional_perf < (1.0 - self.budget.max_traditional_performance_decline):
            cap.status = CapabilityStatus.DORMANT  # Keep but don't promote
            return False, f"performance_decline_too_severe ({traditional_perf:.2f})"
        
        # Update capability
        cap.behavioral_coverage_expansion = coverage_expansion
        cap.traditional_performance = traditional_perf
        cap.validation_runs += 1
        cap.test_results.append({
            'timestamp': datetime.utcnow().isoformat(),
            'results': test_results
        })
        
        # Mark for promotion
        cap.status = CapabilityStatus.PROMOTED
        self.promoted_to_main += 1
        
        # Update coverage tracking
        for dimension in cap.novelty_dimensions:
            self.behavioral_space_coverage.add(dimension)
        
        logger.info(
            f"Capability {capability_id} PROMOTED to main registry: "
            f"coverage_expansion={coverage_expansion:.2f}, "
            f"traditional_perf={traditional_perf:.2f}"
        )
        
        return True, "meets_promotion_criteria"
    
    def get_promotion_candidates(self) -> List[ExploratoryCapability]:
        """Get capabilities ready for promotion consideration"""
        candidates = []
        
        for cap in self.exploratory_registry.values():
            if cap.status == CapabilityStatus.VALIDATING:
                if cap.validation_runs >= 3:  # Minimum test threshold
                    candidates.append(cap)
        
        # Sort by behavioral coverage expansion
        candidates.sort(key=lambda c: c.behavioral_coverage_expansion, reverse=True)
        
        return candidates
    
    def get_exploratory_budget_allocation(self, total_budget: float) -> Dict[str, float]:
        """
        Calculate budget allocation for exploratory vs traditional validation.
        
        Returns allocation split between:
        - exploration: Trying novel capabilities
        - validation: Testing if they work
        """
        novelty_budget = total_budget * self.budget.total_validation_budget_pct
        
        exploration = novelty_budget * self.budget.exploration_to_validation_ratio
        validation = novelty_budget * (1 - self.budget.exploration_to_validation_ratio)
        
        return {
            'novelty_total': novelty_budget,
            'exploration': exploration,
            'validation': validation,
            'traditional': total_budget - novelty_budget
        }
    
    def _evict_oldest_dormant(self):
        """Remove oldest dormant capability if at capacity"""
        dormant = [
            (cid, cap) for cid, cap in self.exploratory_registry.items()
            if cap.status == CapabilityStatus.DORMANT
        ]
        
        if dormant:
            # Sort by created timestamp
            dormant.sort(key=lambda x: x[1].created_timestamp)
            oldest_id = dormant[0][0]
            del self.exploratory_registry[oldest_id]
            logger.info(f"Evicted dormant capability: {oldest_id}")
    
    def get_novelty_search_report(self) -> Dict[str, Any]:
        """Get comprehensive report on novelty search activities"""
        status_counts = defaultdict(int)
        for cap in self.exploratory_registry.values():
            status_counts[cap.status.value] += 1
        
        return {
            'budget_configuration': {
                'total_validation_budget_pct': self.budget.total_validation_budget_pct,
                'exploration_ratio': self.budget.exploration_to_validation_ratio,
                'max_exploratory_capabilities': self.budget.max_exploratory_capabilities
            },
            'statistics': {
                'total_explored': self.total_explored,
                'promoted_to_main': self.promoted_to_main,
                'rejected': self.rejected,
                'currently_exploratory': len(self.exploratory_registry),
                'promotion_rate': self.promoted_to_main / max(1, self.total_explored)
            },
            'registry_status': dict(status_counts),
            'behavioral_space_coverage': {
                'dimensions_covered': len(self.behavioral_space_coverage),
                'dimensions': list(self.behavioral_space_coverage)
            },
            'promotion_candidates': [
                {
                    'id': c.capability_id,
                    'name': c.name,
                    'coverage_expansion': c.behavioral_coverage_expansion,
                    'validation_runs': c.validation_runs
                }
                for c in self.get_promotion_candidates()
            ]
        }


# Factory function
def create_novelty_search_engine(
    validation_budget_pct: float = 0.15
) -> NoveltySearchEngine:
    """Factory function to create novelty search engine"""
    
    budget = NoveltySearchBudget(
        total_validation_budget_pct=validation_budget_pct
    )
    
    return NoveltySearchEngine(budget)
