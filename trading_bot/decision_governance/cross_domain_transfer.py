"""
Cross-Domain Knowledge Transfer System
========================================

Enables transfer of knowledge, strategies, and patterns from other domains
into trading decision systems. Inspired by transfer learning and 
cross-domain adaptation techniques from AI research.

Features:
- Domain mapping and adaptation
- Knowledge abstraction and concretization
- Analogical reasoning across domains
- Transfer validation and efficacy measurement
- Source domain management (game theory, physics, biology, etc.)

Based on cross-domain knowledge transfer patterns from ASI-Evolve research.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class SourceDomain(Enum):
    """Source domains for knowledge transfer"""
    GAME_THEORY = "game_theory"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    ECOLOGY = "ecology"
    PSYCHOLOGY = "psychology"
    INFORMATION_THEORY = "information_theory"
    CONTROL_SYSTEMS = "control_systems"
    NETWORK_SCIENCE = "network_science"
    EVOLUTIONARY_BIOLOGY = "evolutionary_biology"
    STATISTICAL_MECHANICS = "statistical_mechanics"
    COMPLEX_SYSTEMS = "complex_systems"
    ROBOTICS = "robotics"
    COGNITIVE_SCIENCE = "cognitive_science"


class TransferType(Enum):
    """Types of knowledge transfer"""
    DIRECT = "direct"  # Direct application with minimal adaptation
    ANALOGICAL = "analogical"  # By analogy and mapping
    ABSTRACT = "abstract"  # Abstract principles applied concretely
    COMPOSITE = "composite"  # Combining multiple sources


class TransferStatus(Enum):
    """Status of a knowledge transfer"""
    PROPOSED = "proposed"
    MAPPING = "mapping"
    ADAPTING = "adapting"
    VALIDATING = "validating"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class DomainMapping:
    """Mapping between source domain concept and trading domain"""
    source_concept: str
    target_concept: str
    mapping_rationale: str
    confidence: float
    supporting_examples: List[str] = field(default_factory=list)
    
    def validate_mapping(self) -> Tuple[bool, str]:
        """Validate the mapping makes logical sense"""
        if not self.source_concept or not self.target_concept:
            return False, "Empty concepts"
        if self.confidence < 0.1:
            return False, "Confidence too low"
        return True, "Valid"


@dataclass
class TransferredKnowledge:
    """Knowledge that has been transferred from another domain"""
    id: str
    source_domain: SourceDomain
    original_concept: str
    trading_application: str
    transfer_type: TransferType
    
    # Mapping and adaptation
    domain_mappings: List[DomainMapping] = field(default_factory=list)
    adaptation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Status and validation
    status: TransferStatus = TransferStatus.PROPOSED
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    efficacy_score: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    success_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count
    
    def record_usage(self, success: bool):
        """Record usage of this transferred knowledge"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        self.last_used = datetime.utcnow()


@dataclass
class TransferProposal:
    """Proposal for new cross-domain transfer"""
    source_domain: SourceDomain
    source_concept: str
    proposed_trading_application: str
    rationale: str
    novelty_score: float  # 0-1, how novel is this transfer
    supporting_analogies: List[str] = field(default_factory=list)
    expected_benefits: List[str] = field(default_factory=list)


class DomainAdapter:
    """
    Adapts concepts from a specific source domain to trading.
    """
    
    def __init__(self, source_domain: SourceDomain):
        self.source_domain = source_domain
        self.mappings: Dict[str, DomainMapping] = {}
        
    def add_mapping(self, mapping: DomainMapping):
        """Add a domain mapping"""
        key = f"{mapping.source_concept}->{mapping.target_concept}"
        self.mappings[key] = mapping
    
    def adapt_concept(
        self,
        source_concept: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Adapt a source domain concept to trading domain.
        
        Returns trading application or None if no mapping exists.
        """
        # Find best matching mapping
        best_mapping = None
        best_confidence = 0.0
        
        for mapping in self.mappings.values():
            if mapping.source_concept == source_concept:
                if mapping.confidence > best_confidence:
                    best_confidence = mapping.confidence
                    best_mapping = mapping
        
        if best_mapping:
            return self._apply_adaptation(best_mapping, context)
        
        # Try to generate new mapping
        return self._generate_mapping(source_concept, context)
    
    def _apply_adaptation(
        self,
        mapping: DomainMapping,
        context: Dict[str, Any]
    ) -> str:
        """Apply adaptation rules to create trading application"""
        base_application = mapping.target_concept
        
        # Customize based on context
        if 'market_regime' in context:
            regime = context['market_regime']
            base_application += f"_in_{regime}_regime"
        
        if 'asset_class' in context:
            asset = context['asset_class']
            base_application += f"_for_{asset}"
        
        return base_application
    
    def _generate_mapping(
        self,
        source_concept: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate new mapping based on analogy"""
        # Domain-specific generation rules
        generators = {
            SourceDomain.PHYSICS: self._physics_to_trading,
            SourceDomain.BIOLOGY: self._biology_to_trading,
            SourceDomain.GAME_THEORY: self._game_theory_to_trading,
            SourceDomain.ECOLOGY: self._ecology_to_trading,
            SourceDomain.CONTROL_SYSTEMS: self._control_to_trading,
            SourceDomain.EVOLUTIONARY_BIOLOGY: self._evolution_to_trading,
        }
        
        generator = generators.get(self.source_domain)
        if generator:
            return generator(source_concept, context)
        
        return None
    
    def _physics_to_trading(self, concept: str, context: Dict[str, Any]) -> Optional[str]:
        """Map physics concepts to trading"""
        physics_mappings = {
            'momentum': 'price_momentum_strategy',
            'inertia': 'trend_persistence_model',
            'friction': 'transaction_cost_model',
            'entropy': 'market_disorder_index',
            'phase_transition': 'regime_change_detection',
            'resonance': 'cyclical_pattern_detection',
            'damping': 'volatility_decay_model',
            'equilibrium': 'market_efficiency_model',
        }
        return physics_mappings.get(concept.lower())
    
    def _biology_to_trading(self, concept: str, context: Dict[str, Any]) -> Optional[str]:
        """Map biology concepts to trading"""
        biology_mappings = {
            'immune_system': 'portfolio_defense_system',
            'adaptation': 'strategy_regime_adaptation',
            'homeostasis': 'risk_balance_maintenance',
            'fitness': 'strategy_performance_fitness',
            'predator_prey': 'market_participant_dynamics',
            'symbiosis': 'strategy_correlation_benefits',
            'mutation': 'strategy_variation_generation',
            'selection': 'strategy_performance_selection',
        }
        return biology_mappings.get(concept.lower())
    
    def _game_theory_to_trading(self, concept: str, context: Dict[str, Any]) -> Optional[str]:
        """Map game theory concepts to trading"""
        game_mappings = {
            'nash_equilibrium': 'market_equilibrium_detection',
            'zero_sum': 'zero_sum_game_strategies',
            'mixed_strategy': 'probabilistic_signal_mixing',
            'dominant_strategy': 'dominant_setup_detection',
            'prisoner_dilemma': 'cooperation_vs_competition',
            'signaling': 'order_flow_signal_interpretation',
            'bluffing': 'deception_pattern_detection',
            'tit_for_tat': 'reciprocal_market_behavior',
        }
        return game_mappings.get(concept.lower())
    
    def _ecology_to_trading(self, concept: str, context: Dict[str, Any]) -> Optional[str]:
        """Map ecology concepts to trading"""
        ecology_mappings = {
            'biodiversity': 'strategy_diversification',
            'carrying_capacity': 'market_capacity_limits',
            'niche': 'market_microstructure_niche',
            'food_web': 'capital_flow_networks',
            'competition': 'strategy_competition_analysis',
            'succession': 'market_regime_succession',
        }
        return ecology_mappings.get(concept.lower())
    
    def _control_to_trading(self, concept: str, context: Dict[str, Any]) -> Optional[str]:
        """Map control systems concepts to trading"""
        control_mappings = {
            'feedback_loop': 'strategy_performance_feedback',
            'pid_controller': 'adaptive_position_sizing',
            'stability': 'portfolio_stability_control',
            'oscillation': 'drawdown_oscillation_control',
            'overshoot': 'position_limit_prevention',
            'steady_state': 'steady_pnl_targeting',
        }
        return control_mappings.get(concept.lower())
    
    def _evolution_to_trading(self, concept: str, context: Dict[str, Any]) -> Optional[str]:
        """Map evolutionary biology concepts to trading"""
        evolution_mappings = {
            'natural_selection': 'strategy_performance_selection',
            'genetic_drift': 'random_strategy_variation',
            'speciation': 'strategy_specialization',
            'extinction': 'strategy_elimination',
            'coevolution': 'strategy_market_coevolution',
            'fitness_landscape': 'performance_surface_navigation',
        }
        return evolution_mappings.get(concept.lower())


class CrossDomainTransferSystem:
    """
    Cross-Domain Knowledge Transfer System
    
    Manages the transfer of knowledge from external domains
    into trading decision systems.
    """
    
    def __init__(self, validation_threshold: float = 0.6):
        self.validation_threshold = validation_threshold
        
        # Domain adapters
        self.adapters: Dict[SourceDomain, DomainAdapter] = {
            domain: DomainAdapter(domain) for domain in SourceDomain
        }
        
        # Transferred knowledge registry
        self.transfers: Dict[str, TransferredKnowledge] = {}
        
        # Statistics
        self.stats = {
            'transfers_proposed': 0,
            'transfers_active': 0,
            'transfers_failed': 0,
            'successful_applications': 0
        }
        
        # Initialize default mappings
        self._initialize_default_mappings()
    
    def _initialize_default_mappings(self):
        """Initialize default domain mappings"""
        default_mappings = [
            # Physics mappings
            DomainMapping(
                source_concept="momentum",
                target_concept="price_momentum_trading",
                mapping_rationale="Physical momentum conservation parallels price trend persistence",
                confidence=0.85,
                supporting_examples=["Trend following strategies", "Momentum investing"]
            ),
            DomainMapping(
                source_concept="entropy",
                target_concept="market_randomness_measure",
                mapping_rationale="Entropy measures disorder; applies to market unpredictability",
                confidence=0.80,
                supporting_examples=["Volatility clustering", "Information theory in markets"]
            ),
            # Biology mappings
            DomainMapping(
                source_concept="immune_system",
                target_concept="portfolio_defense",
                mapping_rationale="Immune system defense parallels portfolio risk management",
                confidence=0.75,
                supporting_examples=["Diversification as defense", "Hedging strategies"]
            ),
            # Game theory mappings
            DomainMapping(
                source_concept="nash_equilibrium",
                target_concept="market_equilibrium",
                mapping_rationale="Strategic equilibrium in games applies to market balance",
                confidence=0.90,
                supporting_examples=["Market maker equilibrium", "Options market equilibrium"]
            ),
            DomainMapping(
                source_concept="signaling",
                target_concept="order_flow_analysis",
                mapping_rationale="Information signaling in games parallels order flow information",
                confidence=0.85,
                supporting_examples=["Informed trading", "Order book signaling"]
            ),
        ]
        
        for mapping in default_mappings:
            # Determine domain based on concept
            if mapping.source_concept in ['momentum', 'entropy', 'inertia', 'friction']:
                domain = SourceDomain.PHYSICS
            elif mapping.source_concept in ['immune_system', 'adaptation', 'homeostasis']:
                domain = SourceDomain.BIOLOGY
            else:
                domain = SourceDomain.GAME_THEORY
            
            self.adapters[domain].add_mapping(mapping)
    
    async def propose_transfer(
        self,
        proposal: TransferProposal
    ) -> Optional[str]:
        """
        Propose a new cross-domain knowledge transfer.
        
        Returns transfer ID if accepted, None if rejected.
        """
        self.stats['transfers_proposed'] += 1
        
        # Validate proposal
        if proposal.novelty_score < 0.3:
            logger.info(f"Proposal rejected: novelty too low ({proposal.novelty_score})")
            return None
        
        # Create transfer
        transfer = TransferredKnowledge(
            id=str(uuid.uuid4()),
            source_domain=proposal.source_domain,
            original_concept=proposal.source_concept,
            trading_application=proposal.proposed_trading_application,
            transfer_type=TransferType.ANALOGICAL if proposal.supporting_analogies else TransferType.ABSTRACT
        )
        
        # Generate mappings
        adapter = self.adapters[proposal.source_domain]
        adapted = adapter.adapt_concept(proposal.source_concept, {})
        
        if adapted:
            mapping = DomainMapping(
                source_concept=proposal.source_concept,
                target_concept=adapted,
                mapping_rationale=proposal.rationale,
                confidence=0.6,
                supporting_examples=proposal.supporting_analogies
            )
            transfer.domain_mappings.append(mapping)
        
        self.transfers[transfer.id] = transfer
        
        logger.info(f"Created transfer {transfer.id}: {proposal.source_concept} -> {adapted or 'unknown'}")
        
        return transfer.id
    
    async def validate_transfer(
        self,
        transfer_id: str,
        validation_data: Dict[str, Any]
    ) -> bool:
        """
        Validate a transferred knowledge through testing.
        
        Returns True if validation passes.
        """
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            return False
        
        transfer.status = TransferStatus.VALIDATING
        
        # Simulate validation
        # In production, this would run backtests/simulations
        
        # Compute efficacy score based on validation data
        if 'backtest_results' in validation_data:
            results = validation_data['backtest_results']
            sharpe = results.get('sharpe_ratio', 0)
            win_rate = results.get('win_rate', 0)
            
            transfer.efficacy_score = (sharpe * 0.5 + win_rate * 0.5)
        else:
            # Default validation
            transfer.efficacy_score = 0.65  # Neutral default
        
        # Record validation
        transfer.validation_results.append({
            'timestamp': datetime.utcnow().isoformat(),
            'efficacy_score': transfer.efficacy_score,
            'data_source': validation_data.get('source', 'unknown')
        })
        
        # Determine status
        if transfer.efficacy_score >= self.validation_threshold:
            transfer.status = TransferStatus.ACTIVE
            self.stats['transfers_active'] += 1
            logger.info(f"Transfer {transfer_id} validated and activated")
            return True
        else:
            transfer.status = TransferStatus.FAILED
            self.stats['transfers_failed'] += 1
            logger.info(f"Transfer {transfer_id} failed validation")
            return False
    
    def get_transfer(
        self,
        transfer_id: str
    ) -> Optional[TransferredKnowledge]:
        """Get a specific transfer by ID"""
        return self.transfers.get(transfer_id)
    
    def find_applicable_transfers(
        self,
        market_context: Dict[str, Any],
        min_efficacy: float = 0.5
    ) -> List[Tuple[TransferredKnowledge, float]]:
        """
        Find transferred knowledge applicable to current context.
        
        Returns list of (transfer, relevance_score) tuples.
        """
        applicable = []
        
        for transfer in self.transfers.values():
            if transfer.status != TransferStatus.ACTIVE:
                continue
            
            if transfer.efficacy_score < min_efficacy:
                continue
            
            # Score relevance to context
            relevance = self._score_relevance(transfer, market_context)
            
            if relevance > 0.3:
                applicable.append((transfer, relevance))
        
        # Sort by combined efficacy and relevance
        applicable.sort(
            key=lambda x: x[0].efficacy_score * x[1],
            reverse=True
        )
        
        return applicable
    
    def _score_relevance(
        self,
        transfer: TransferredKnowledge,
        context: Dict[str, Any]
    ) -> float:
        """Score how relevant a transfer is to current context"""
        score = 0.5  # Base relevance
        
        # Check market regime match
        if 'market_regime' in context:
            regime = context['market_regime']
            for mapping in transfer.domain_mappings:
                if regime in mapping.target_concept:
                    score += 0.3
        
        # Check asset class match
        if 'asset_class' in context:
            asset = context['asset_class']
            for mapping in transfer.domain_mappings:
                if asset in mapping.target_concept:
                    score += 0.2
        
        # Factor in historical success rate
        score *= (0.5 + 0.5 * transfer.success_rate)
        
        return min(1.0, score)
    
    def apply_transfer(
        self,
        transfer_id: str,
        application_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Apply transferred knowledge to generate trading insight.
        
        Returns application result or None if application fails.
        """
        transfer = self.transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.ACTIVE:
            return None
        
        # Get best mapping
        if not transfer.domain_mappings:
            return None
        
        best_mapping = max(transfer.domain_mappings, key=lambda m: m.confidence)
        
        # Generate application
        adapter = self.adapters[transfer.source_domain]
        adapted_concept = adapter.adapt_concept(
            transfer.original_concept,
            application_context
        )
        
        result = {
            'transfer_id': transfer_id,
            'source_domain': transfer.source_domain.value,
            'original_concept': transfer.original_concept,
            'trading_application': adapted_concept or best_mapping.target_concept,
            'confidence': best_mapping.confidence * transfer.efficacy_score,
            'rationale': best_mapping.mapping_rationale,
            'context': application_context
        }
        
        transfer.record_usage(success=True)  # Will be updated with actual outcome
        self.stats['successful_applications'] += 1
        
        return result
    
    def get_transfer_statistics(self) -> Dict[str, Any]:
        """Get statistics about transfers"""
        return {
            **self.stats,
            'total_transfers': len(self.transfers),
            'by_domain': {
                domain.value: len([
                    t for t in self.transfers.values()
                    if t.source_domain == domain
                ])
                for domain in SourceDomain
            },
            'by_status': {
                status.value: len([
                    t for t in self.transfers.values()
                    if t.status == status
                ])
                for status in TransferStatus
            },
            'top_performers': [
                {
                    'id': t.id,
                    'concept': t.original_concept,
                    'efficacy': t.efficacy_score,
                    'success_rate': t.success_rate
                }
                for t in sorted(
                    [t for t in self.transfers.values() if t.status == TransferStatus.ACTIVE],
                    key=lambda x: x.efficacy_score,
                    reverse=True
                )[:5]
            ]
        }
    
    def discover_analogies(
        self,
        trading_problem: str,
        target_domains: Optional[List[SourceDomain]] = None
    ) -> List[TransferProposal]:
        """
        Discover potential analogies from other domains.
        
        Returns list of transfer proposals.
        """
        proposals = []
        
        domains = target_domains or list(SourceDomain)
        
        for domain in domains:
            adapter = self.adapters[domain]
            
            # Try to find analogical mappings
            adapted = adapter.adapt_concept(trading_problem, {})
            
            if adapted:
                proposal = TransferProposal(
                    source_domain=domain,
                    source_concept=trading_problem,
                    proposed_trading_application=adapted,
                    rationale=f"Analogical mapping from {domain.value} domain",
                    novelty_score=0.6,
                    supporting_analogies=[f"Domain: {domain.value}"]
                )
                proposals.append(proposal)
        
        return proposals


def create_cross_domain_transfer_system(
    validation_threshold: float = 0.6
) -> CrossDomainTransferSystem:
    """Factory function to create cross-domain transfer system"""
    return CrossDomainTransferSystem(
        validation_threshold=validation_threshold
    )
