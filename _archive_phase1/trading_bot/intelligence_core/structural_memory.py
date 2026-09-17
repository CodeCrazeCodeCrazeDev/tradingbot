"""
Structural Memory System
=========================

AI remembers mistakes STRUCTURALLY, not statistically.

PHILOSOPHY:
- Remember WHY decisions failed, not just THAT they failed
- Build causal graphs of failure modes
- Detect recurring structural patterns
- Never forget failure mechanisms
- Learn from the STRUCTURE of mistakes, not just their frequency

STRUCTURAL vs STATISTICAL MEMORY:
❌ STATISTICAL: "This strategy failed 40% of the time"
✅ STRUCTURAL: "This strategy fails WHEN volatility spikes during low liquidity
                BECAUSE the stop-loss gets hit by spread widening
                WHICH CAUSES cascading losses
                SIMILAR TO the 2020-03-12 flash crash pattern"

MEMORY TYPES:
1. FAILURE MECHANISMS - How things break
2. CAUSAL CHAINS - What leads to what
3. STRUCTURAL PATTERNS - Recurring failure shapes
4. REGIME SIGNATURES - What conditions cause failures
5. RECOVERY PATHS - How to recover from failures
"""

import logging
import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class FailureSeverity(Enum):
    """Severity of failure"""
    MINOR = "minor"             # Small loss, recoverable
    MODERATE = "moderate"       # Significant loss
    SEVERE = "severe"           # Large loss
    CATASTROPHIC = "catastrophic"  # System-threatening


class FailureCategory(Enum):
    """Category of failure"""
    MODEL_FAILURE = "model_failure"           # Model prediction wrong
    EXECUTION_FAILURE = "execution_failure"   # Execution problem
    REGIME_FAILURE = "regime_failure"         # Regime change
    LIQUIDITY_FAILURE = "liquidity_failure"   # Liquidity crisis
    CORRELATION_FAILURE = "correlation_failure"  # Correlation breakdown
    TIMING_FAILURE = "timing_failure"         # Wrong timing
    SIZING_FAILURE = "sizing_failure"         # Wrong position size
    RISK_FAILURE = "risk_failure"             # Risk management failure
    DATA_FAILURE = "data_failure"             # Data quality issue
    UNKNOWN = "unknown"                       # Unknown cause


@dataclass
class CausalNode:
    """A node in the causal graph"""
    node_id: str
    description: str
    node_type: str  # 'cause', 'effect', 'condition', 'mechanism'
    timestamp: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'description': self.description,
            'node_type': self.node_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'data': self.data
        }


@dataclass
class CausalEdge:
    """An edge in the causal graph"""
    from_node: str
    to_node: str
    relationship: str  # 'causes', 'enables', 'prevents', 'correlates'
    strength: float    # 0 to 1
    confidence: float  # 0 to 1
    evidence_count: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'from_node': self.from_node,
            'to_node': self.to_node,
            'relationship': self.relationship,
            'strength': self.strength,
            'confidence': self.confidence,
            'evidence_count': self.evidence_count
        }


@dataclass
class CausalGraph:
    """Causal graph representing failure mechanism"""
    graph_id: str
    name: str
    description: str
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: List[CausalEdge] = field(default_factory=list)
    root_causes: List[str] = field(default_factory=list)
    final_effects: List[str] = field(default_factory=list)
    
    def add_node(self, node: CausalNode):
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: CausalEdge):
        self.edges.append(edge)
    
    def get_causes_of(self, node_id: str) -> List[str]:
        """Get all direct causes of a node"""
        return [e.from_node for e in self.edges if e.to_node == node_id]
    
    def get_effects_of(self, node_id: str) -> List[str]:
        """Get all direct effects of a node"""
        return [e.to_node for e in self.edges if e.from_node == node_id]
    
    def get_root_cause_chain(self, effect_id: str) -> List[str]:
        """Trace back to root causes"""
        chain = []
        visited = set()
        queue = [effect_id]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            chain.append(current)
            
            causes = self.get_causes_of(current)
            queue.extend(causes)
        
        return chain
    
    def to_dict(self) -> Dict:
        return {
            'graph_id': self.graph_id,
            'name': self.name,
            'description': self.description,
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'edges': [e.to_dict() for e in self.edges],
            'root_causes': self.root_causes,
            'final_effects': self.final_effects
        }


@dataclass
class StructuralPattern:
    """A recurring structural pattern in failures"""
    pattern_id: str
    name: str
    description: str
    
    # Pattern definition
    trigger_conditions: List[str]      # What triggers this pattern
    mechanism: str                      # How it unfolds
    typical_sequence: List[str]         # Typical event sequence
    warning_signs: List[str]            # Early warning signs
    
    # Statistics
    occurrence_count: int = 0
    last_occurrence: Optional[datetime] = None
    avg_severity: float = 0.0
    avg_loss: float = 0.0
    
    # Similar patterns
    similar_patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'name': self.name,
            'description': self.description,
            'trigger_conditions': self.trigger_conditions,
            'mechanism': self.mechanism,
            'typical_sequence': self.typical_sequence,
            'warning_signs': self.warning_signs,
            'occurrence_count': self.occurrence_count,
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'avg_severity': self.avg_severity,
            'avg_loss': self.avg_loss,
            'similar_patterns': self.similar_patterns
        }


@dataclass
class FailureMemory:
    """Complete memory of a failure"""
    memory_id: str
    timestamp: datetime
    
    # What happened
    description: str
    category: FailureCategory
    severity: FailureSeverity
    
    # Context
    market_conditions: Dict[str, Any]
    strategy_state: Dict[str, Any]
    position_state: Dict[str, Any]
    
    # Structural analysis
    causal_graph: Optional[CausalGraph] = None
    matched_patterns: List[str] = field(default_factory=list)
    
    # Why it happened
    root_causes: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    
    # Impact
    loss_amount: float = 0.0
    loss_percentage: float = 0.0
    recovery_time: Optional[str] = None
    
    # Lessons
    lessons_learned: List[str] = field(default_factory=list)
    prevention_measures: List[str] = field(default_factory=list)
    
    # Metadata
    analyzed: bool = False
    reviewed_by_human: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'memory_id': self.memory_id,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'category': self.category.value,
            'severity': self.severity.value,
            'market_conditions': self.market_conditions,
            'strategy_state': self.strategy_state,
            'position_state': self.position_state,
            'causal_graph': self.causal_graph.to_dict() if self.causal_graph else None,
            'matched_patterns': self.matched_patterns,
            'root_causes': self.root_causes,
            'contributing_factors': self.contributing_factors,
            'loss_amount': self.loss_amount,
            'loss_percentage': self.loss_percentage,
            'recovery_time': self.recovery_time,
            'lessons_learned': self.lessons_learned,
            'prevention_measures': self.prevention_measures,
            'analyzed': self.analyzed,
            'reviewed_by_human': self.reviewed_by_human
        }


class CausalAnalyzer:
    """Analyzes failures to build causal graphs"""
    
    def __init__(self):
        self.known_mechanisms: Dict[str, List[str]] = {
            'volatility_spike': [
                'spread_widening',
                'stop_loss_triggered',
                'slippage_increase',
                'liquidity_drop'
            ],
            'liquidity_crisis': [
                'order_rejection',
                'partial_fills',
                'price_gaps',
                'execution_delay'
            ],
            'regime_change': [
                'correlation_breakdown',
                'model_invalidation',
                'strategy_failure',
                'risk_model_failure'
            ],
            'flash_crash': [
                'cascade_selling',
                'stop_hunting',
                'liquidity_vacuum',
                'price_dislocation'
            ]
        }
    
    def analyze(
        self,
        failure: FailureMemory,
        historical_data: Optional[Dict] = None
    ) -> CausalGraph:
        """
        Analyze a failure and build causal graph.
        
        Args:
            failure: The failure to analyze
            historical_data: Optional historical context
            
        Returns:
            CausalGraph representing the failure mechanism
        """
        graph_id = hashlib.md5(
            f"{failure.memory_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        graph = CausalGraph(
            graph_id=graph_id,
            name=f"Failure Analysis: {failure.description[:50]}",
            description=failure.description
        )
        
        # Identify root causes from market conditions
        root_causes = self._identify_root_causes(failure)
        
        # Build causal chain
        for i, cause in enumerate(root_causes):
            node = CausalNode(
                node_id=f"cause_{i}",
                description=cause,
                node_type='cause',
                timestamp=failure.timestamp
            )
            graph.add_node(node)
            graph.root_causes.append(node.node_id)
        
        # Add mechanism nodes
        mechanism_nodes = self._identify_mechanism(failure)
        for i, mech in enumerate(mechanism_nodes):
            node = CausalNode(
                node_id=f"mechanism_{i}",
                description=mech,
                node_type='mechanism'
            )
            graph.add_node(node)
        
        # Add effect nodes
        effect = CausalNode(
            node_id="final_effect",
            description=f"Loss: {failure.loss_percentage:.2%}",
            node_type='effect',
            timestamp=failure.timestamp
        )
        graph.add_node(effect)
        graph.final_effects.append(effect.node_id)
        
        # Connect nodes
        self._connect_nodes(graph, root_causes, mechanism_nodes)
        
        return graph
    
    def _identify_root_causes(self, failure: FailureMemory) -> List[str]:
        """Identify root causes from failure context"""
        causes = []
        
        conditions = failure.market_conditions
        
        # Check for volatility
        if conditions.get('volatility', 0) > conditions.get('avg_volatility', 0) * 2:
            causes.append("Volatility spike (>2x average)")
        
        # Check for liquidity
        if conditions.get('liquidity', 'normal') in ['low', 'very_low']:
            causes.append("Low liquidity conditions")
        
        # Check for regime
        if conditions.get('regime_change', False):
            causes.append("Regime change detected")
        
        # Check for correlation
        if conditions.get('correlation_breakdown', False):
            causes.append("Correlation breakdown")
        
        # Check for news/events
        if conditions.get('major_news', False):
            causes.append("Major news event")
        
        if not causes:
            causes.append("Unknown root cause - requires investigation")
        
        return causes
    
    def _identify_mechanism(self, failure: FailureMemory) -> List[str]:
        """Identify the mechanism of failure"""
        mechanisms = []
        
        category = failure.category
        
        if category == FailureCategory.EXECUTION_FAILURE:
            mechanisms = ['Order rejected', 'Slippage exceeded', 'Partial fill']
        elif category == FailureCategory.REGIME_FAILURE:
            mechanisms = ['Model assumptions violated', 'Strategy edge disappeared']
        elif category == FailureCategory.LIQUIDITY_FAILURE:
            mechanisms = ['Spread widened', 'No counterparty', 'Price gapped']
        elif category == FailureCategory.MODEL_FAILURE:
            mechanisms = ['Prediction wrong', 'Confidence miscalibrated']
        else:
            mechanisms = ['Unknown mechanism']
        
        return mechanisms
    
    def _connect_nodes(
        self,
        graph: CausalGraph,
        root_causes: List[str],
        mechanisms: List[str]
    ):
        """Connect nodes in the causal graph"""
        # Connect causes to mechanisms
        for i, cause in enumerate(root_causes):
            for j, mech in enumerate(mechanisms):
                edge = CausalEdge(
                    from_node=f"cause_{i}",
                    to_node=f"mechanism_{j}",
                    relationship='causes',
                    strength=0.7,
                    confidence=0.6
                )
                graph.add_edge(edge)
        
        # Connect mechanisms to effect
        for j in range(len(mechanisms)):
            edge = CausalEdge(
                from_node=f"mechanism_{j}",
                to_node="final_effect",
                relationship='causes',
                strength=0.8,
                confidence=0.7
            )
            graph.add_edge(edge)


class PatternMatcher:
    """Matches failures to known structural patterns"""
    
    def __init__(self):
        self.patterns: Dict[str, StructuralPattern] = {}
        self._initialize_known_patterns()
    
    def _initialize_known_patterns(self):
        """Initialize known failure patterns"""
        
        # Flash crash pattern
        self.patterns['flash_crash'] = StructuralPattern(
            pattern_id='flash_crash',
            name='Flash Crash Pattern',
            description='Rapid price decline followed by recovery',
            trigger_conditions=[
                'High volatility',
                'Low liquidity',
                'Cascade of stop losses'
            ],
            mechanism='Stop losses trigger more selling, creating liquidity vacuum',
            typical_sequence=[
                'Initial price drop',
                'Stop losses triggered',
                'Liquidity disappears',
                'Price gaps down',
                'Recovery begins'
            ],
            warning_signs=[
                'Unusual volume spike',
                'Bid depth thinning',
                'Spread widening'
            ]
        )
        
        # Regime change pattern
        self.patterns['regime_change'] = StructuralPattern(
            pattern_id='regime_change',
            name='Regime Change Pattern',
            description='Market transitions to new regime, invalidating models',
            trigger_conditions=[
                'Correlation breakdown',
                'Volatility regime shift',
                'Macro event'
            ],
            mechanism='Historical relationships break down, models fail',
            typical_sequence=[
                'Unusual correlation behavior',
                'Model predictions diverge from reality',
                'Strategy performance degrades',
                'Multiple consecutive losses'
            ],
            warning_signs=[
                'Correlation instability',
                'Increasing prediction errors',
                'Unusual market behavior'
            ]
        )
        
        # Liquidity trap pattern
        self.patterns['liquidity_trap'] = StructuralPattern(
            pattern_id='liquidity_trap',
            name='Liquidity Trap Pattern',
            description='Position cannot be exited at reasonable price',
            trigger_conditions=[
                'Large position relative to market',
                'Sudden liquidity drop',
                'One-sided market'
            ],
            mechanism='Exit attempts move market against position',
            typical_sequence=[
                'Position established',
                'Liquidity dries up',
                'Exit attempts fail or cause slippage',
                'Forced to hold or accept large loss'
            ],
            warning_signs=[
                'Decreasing volume',
                'Widening spreads',
                'Order book thinning'
            ]
        )
        
        # Overfit pattern
        self.patterns['overfit_failure'] = StructuralPattern(
            pattern_id='overfit_failure',
            name='Overfit Failure Pattern',
            description='Model performs well in backtest, fails live',
            trigger_conditions=[
                'Model trained on limited data',
                'Too many parameters',
                'Data snooping'
            ],
            mechanism='Model learned noise, not signal',
            typical_sequence=[
                'Excellent backtest results',
                'Initial live performance matches',
                'Performance degrades over time',
                'Consistent losses'
            ],
            warning_signs=[
                'Too-good-to-be-true backtest',
                'High parameter count',
                'Sensitivity to small changes'
            ]
        )
    
    def match(self, failure: FailureMemory) -> List[Tuple[str, float]]:
        """
        Match failure to known patterns.
        
        Returns:
            List of (pattern_id, confidence) tuples
        """
        matches = []
        
        for pattern_id, pattern in self.patterns.items():
            confidence = self._calculate_match_confidence(failure, pattern)
            if confidence > 0.3:
                matches.append((pattern_id, confidence))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def _calculate_match_confidence(
        self,
        failure: FailureMemory,
        pattern: StructuralPattern
    ) -> float:
        """Calculate confidence that failure matches pattern"""
        score = 0.0
        max_score = 0.0
        
        # Check trigger conditions
        conditions = failure.market_conditions
        for trigger in pattern.trigger_conditions:
            max_score += 1.0
            trigger_lower = trigger.lower()
            
            if 'volatility' in trigger_lower and conditions.get('high_volatility', False):
                score += 1.0
            elif 'liquidity' in trigger_lower and conditions.get('low_liquidity', False):
                score += 1.0
            elif 'correlation' in trigger_lower and conditions.get('correlation_breakdown', False):
                score += 1.0
            elif 'regime' in trigger_lower and conditions.get('regime_change', False):
                score += 1.0
        
        # Check warning signs
        for sign in pattern.warning_signs:
            max_score += 0.5
            sign_lower = sign.lower()
            
            if 'volume' in sign_lower and conditions.get('unusual_volume', False):
                score += 0.5
            elif 'spread' in sign_lower and conditions.get('spread_widening', False):
                score += 0.5
        
        if max_score == 0:
            return 0.0
        
        return score / max_score
    
    def get_pattern(self, pattern_id: str) -> Optional[StructuralPattern]:
        """Get pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def add_pattern(self, pattern: StructuralPattern):
        """Add new pattern"""
        self.patterns[pattern.pattern_id] = pattern


class StructuralMemory:
    """
    Main structural memory system.
    
    CORE PRINCIPLE:
    Remember mistakes STRUCTURALLY, not statistically.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Memory storage
        self.memories: Dict[str, FailureMemory] = {}
        self.causal_graphs: Dict[str, CausalGraph] = {}
        
        # Analysis tools
        self.causal_analyzer = CausalAnalyzer()
        self.pattern_matcher = PatternMatcher()
        
        # Pattern statistics
        self.pattern_occurrences: Dict[str, int] = defaultdict(int)
        
        # Statistics
        self.total_failures = 0
        self.total_analyzed = 0
        self.patterns_detected = 0
        
        logger.info("StructuralMemory initialized")
    
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
        
        Args:
            description: What happened
            category: Category of failure
            severity: Severity level
            market_conditions: Market state at failure
            strategy_state: Strategy state at failure
            position_state: Position state at failure
            loss_amount: Absolute loss
            loss_percentage: Percentage loss
            
        Returns:
            Memory ID
        """
        with self.lock:
            memory_id = hashlib.md5(
                f"{description}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            memory = FailureMemory(
                memory_id=memory_id,
                timestamp=datetime.now(),
                description=description,
                category=category,
                severity=severity,
                market_conditions=market_conditions,
                strategy_state=strategy_state,
                position_state=position_state,
                loss_amount=loss_amount,
                loss_percentage=loss_percentage
            )
            
            self.memories[memory_id] = memory
            self.total_failures += 1
            
            logger.info(
                "Recorded failure %s: %s [%s/%s]",
                memory_id,
                description[:50],
                category.value,
                severity.value
            )
            
            return memory_id
    
    def analyze_failure(self, memory_id: str) -> Optional[FailureMemory]:
        """
        Analyze a failure structurally.
        
        Args:
            memory_id: ID of failure to analyze
            
        Returns:
            Analyzed failure memory
        """
        with self.lock:
            if memory_id not in self.memories:
                logger.error("Memory %s not found", memory_id)
                return None
            
            memory = self.memories[memory_id]
            
            # Build causal graph
            causal_graph = self.causal_analyzer.analyze(memory)
            memory.causal_graph = causal_graph
            self.causal_graphs[causal_graph.graph_id] = causal_graph
            
            # Extract root causes
            memory.root_causes = [
                self.causal_graphs[causal_graph.graph_id].nodes[rc].description
                for rc in causal_graph.root_causes
                if rc in causal_graph.nodes
            ]
            
            # Match to patterns
            matches = self.pattern_matcher.match(memory)
            memory.matched_patterns = [m[0] for m in matches]
            
            # Update pattern statistics
            for pattern_id, confidence in matches:
                self.pattern_occurrences[pattern_id] += 1
                self.patterns_detected += 1
                
                # Update pattern statistics
                pattern = self.pattern_matcher.get_pattern(pattern_id)
                if pattern:
                    pattern.occurrence_count += 1
                    pattern.last_occurrence = datetime.now()
            
            # Generate lessons
            memory.lessons_learned = self._generate_lessons(memory)
            memory.prevention_measures = self._generate_prevention(memory)
            
            memory.analyzed = True
            self.total_analyzed += 1
            
            logger.info(
                "Analyzed failure %s: %d root causes, %d patterns matched",
                memory_id,
                len(memory.root_causes),
                len(memory.matched_patterns)
            )
            
            return memory
    
    def _generate_lessons(self, memory: FailureMemory) -> List[str]:
        """Generate lessons from failure"""
        lessons = []
        
        # From root causes
        for cause in memory.root_causes:
            lessons.append(f"Monitor for: {cause}")
        
        # From patterns
        for pattern_id in memory.matched_patterns:
            pattern = self.pattern_matcher.get_pattern(pattern_id)
            if pattern:
                lessons.append(f"Pattern '{pattern.name}' detected - review warning signs")
        
        # From category
        if memory.category == FailureCategory.REGIME_FAILURE:
            lessons.append("Implement regime detection before trading")
        elif memory.category == FailureCategory.LIQUIDITY_FAILURE:
            lessons.append("Check liquidity before entering positions")
        elif memory.category == FailureCategory.MODEL_FAILURE:
            lessons.append("Review model assumptions and validation")
        
        return lessons
    
    def _generate_prevention(self, memory: FailureMemory) -> List[str]:
        """Generate prevention measures"""
        measures = []
        
        # From patterns
        for pattern_id in memory.matched_patterns:
            pattern = self.pattern_matcher.get_pattern(pattern_id)
            if pattern:
                for sign in pattern.warning_signs:
                    measures.append(f"Add alert for: {sign}")
        
        # From severity
        if memory.severity in [FailureSeverity.SEVERE, FailureSeverity.CATASTROPHIC]:
            measures.append("Add hard stop for similar conditions")
            measures.append("Reduce position size in similar scenarios")
        
        return measures
    
    def find_similar_failures(
        self,
        memory_id: str,
        min_similarity: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Find failures similar to given one.
        
        Args:
            memory_id: ID of reference failure
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (memory_id, similarity) tuples
        """
        with self.lock:
            if memory_id not in self.memories:
                return []
            
            reference = self.memories[memory_id]
            similar = []
            
            for other_id, other in self.memories.items():
                if other_id == memory_id:
                    continue
                
                similarity = self._calculate_similarity(reference, other)
                if similarity >= min_similarity:
                    similar.append((other_id, similarity))
            
            similar.sort(key=lambda x: x[1], reverse=True)
            return similar
    
    def _calculate_similarity(
        self,
        mem1: FailureMemory,
        mem2: FailureMemory
    ) -> float:
        """Calculate structural similarity between failures"""
        score = 0.0
        
        # Same category
        if mem1.category == mem2.category:
            score += 0.3
        
        # Same severity
        if mem1.severity == mem2.severity:
            score += 0.1
        
        # Overlapping patterns
        patterns1 = set(mem1.matched_patterns)
        patterns2 = set(mem2.matched_patterns)
        if patterns1 and patterns2:
            overlap = len(patterns1 & patterns2) / len(patterns1 | patterns2)
            score += 0.3 * overlap
        
        # Similar root causes
        causes1 = set(mem1.root_causes)
        causes2 = set(mem2.root_causes)
        if causes1 and causes2:
            # Simple keyword matching
            words1 = set(' '.join(causes1).lower().split())
            words2 = set(' '.join(causes2).lower().split())
            if words1 and words2:
                overlap = len(words1 & words2) / len(words1 | words2)
                score += 0.3 * overlap
        
        return min(1.0, score)
    
    def get_recurring_patterns(self, min_occurrences: int = 2) -> List[StructuralPattern]:
        """Get patterns that occur frequently"""
        with self.lock:
            recurring = []
            
            for pattern_id, count in self.pattern_occurrences.items():
                if count >= min_occurrences:
                    pattern = self.pattern_matcher.get_pattern(pattern_id)
                    if pattern:
                        recurring.append(pattern)
            
            recurring.sort(key=lambda p: p.occurrence_count, reverse=True)
            return recurring
    
    def get_failure_by_pattern(self, pattern_id: str) -> List[FailureMemory]:
        """Get all failures matching a pattern"""
        with self.lock:
            return [
                mem for mem in self.memories.values()
                if pattern_id in mem.matched_patterns
            ]
    
    def get_memory(self, memory_id: str) -> Optional[FailureMemory]:
        """Get failure memory by ID"""
        with self.lock:
            return self.memories.get(memory_id)
    
    def get_all_memories(self) -> List[FailureMemory]:
        """Get all failure memories"""
        with self.lock:
            return list(self.memories.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        with self.lock:
            return {
                'total_failures': self.total_failures,
                'total_analyzed': self.total_analyzed,
                'patterns_detected': self.patterns_detected,
                'unique_patterns': len(self.pattern_occurrences),
                'pattern_distribution': dict(self.pattern_occurrences),
                'category_distribution': self._get_category_distribution(),
                'severity_distribution': self._get_severity_distribution()
            }
    
    def _get_category_distribution(self) -> Dict[str, int]:
        """Get distribution of failure categories"""
        dist = defaultdict(int)
        for mem in self.memories.values():
            dist[mem.category.value] += 1
        return dict(dist)
    
    def _get_severity_distribution(self) -> Dict[str, int]:
        """Get distribution of failure severities"""
        dist = defaultdict(int)
        for mem in self.memories.values():
            dist[mem.severity.value] += 1
        return dict(dist)
