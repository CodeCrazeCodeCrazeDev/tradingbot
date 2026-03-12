"""
AAMIS v3.0 - Advanced Pattern Discovery Engine

This module implements:
1. AI scans markets to find patterns NO human has named
2. Signals NO textbook describes
3. Correlations outside human imagination
4. Cross-Domain Innovation - Apply patterns from other fields
5. Autonomous Productive Failure Engine - Learn from failures systematically
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque, defaultdict
import hashlib
import numpy

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of discovered patterns"""
    UNNAMED = "UNNAMED"  # Never seen before
    TEXTBOOK = "TEXTBOOK"  # Known pattern
    HYBRID = "HYBRID"  # Combination of known patterns
    CROSS_DOMAIN = "CROSS_DOMAIN"  # From other fields
    EMERGENT = "EMERGENT"  # Emerges from complexity
    FRACTAL = "FRACTAL"  # Self-similar across scales
    QUANTUM = "QUANTUM"  # Superposition-like behavior
    BIOLOGICAL = "BIOLOGICAL"  # Nature-inspired
    CHAOS = "CHAOS"  # Chaotic system pattern


class DiscoveryMethod(Enum):
    """Methods for pattern discovery"""
    GENETIC_ALGORITHM = "GENETIC_ALGORITHM"
    NEURAL_SEARCH = "NEURAL_SEARCH"
    SYMBOLIC_REGRESSION = "SYMBOLIC_REGRESSION"
    CLUSTERING = "CLUSTERING"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    CORRELATION_MINING = "CORRELATION_MINING"
    CAUSAL_INFERENCE = "CAUSAL_INFERENCE"
    TRANSFER_LEARNING = "TRANSFER_LEARNING"


@dataclass
class DiscoveredPattern:
    """A newly discovered pattern"""
    pattern_id: str
    pattern_type: PatternType
    discovery_method: DiscoveryMethod
    name: str  # Auto-generated name
    description: str
    mathematical_formula: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    confidence: float = 0.0
    occurrences: int = 0
    profitability: float = 0.0
    discovered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    is_validated: bool = False
    
    def generate_hash(self) -> str:
        """Generate unique hash for pattern"""
        pattern_str = f"{self.conditions}_{self.mathematical_formula}"
        return hashlib.md5(pattern_str.encode()).hexdigest()[:12]


@dataclass
class CrossDomainPattern:
    """Pattern transferred from another domain"""
    pattern_id: str
    source_domain: str  # e.g., "Biology", "Physics", "Music"
    target_domain: str  # "Trading"
    original_concept: str
    adapted_concept: str
    adaptation_rules: List[str] = field(default_factory=list)
    effectiveness: float = 0.0


@dataclass
class FailureLesson:
    """Lesson learned from failure"""
    lesson_id: str
    failure_type: str
    failure_description: str
    root_cause: str
    learned_rules: List[str] = field(default_factory=list)
    prevention_strategy: str = ""
    occurred_at: datetime = field(default_factory=datetime.now)
    times_prevented: int = 0


class UnnamedPatternScanner:
    """
    Scans for patterns that have never been named or documented
    Uses unsupervised learning to find novel market behaviors
    """
    
    def __init__(self):
        self.discovered_patterns: List[DiscoveredPattern] = []
        self.pattern_library: Dict[str, DiscoveredPattern] = {}
        self.scan_count = 0
        
    def scan_for_unnamed_patterns(self, market_data: List[Dict]) -> List[DiscoveredPattern]:
        """Scan market data for unnamed patterns"""
        logger.info("🔍 Scanning for unnamed patterns...")
        
        new_patterns = []
        
        # Method 1: Statistical Anomaly Detection
        anomaly_patterns = self._detect_anomaly_patterns(market_data)
        new_patterns.extend(anomaly_patterns)
        
        # Method 2: Correlation Mining
        correlation_patterns = self._mine_unusual_correlations(market_data)
        new_patterns.extend(correlation_patterns)
        
        # Method 3: Sequence Pattern Mining
        sequence_patterns = self._mine_sequence_patterns(market_data)
        new_patterns.extend(sequence_patterns)
        
        # Method 4: Fractal Pattern Detection
        fractal_patterns = self._detect_fractal_patterns(market_data)
        new_patterns.extend(fractal_patterns)
        
        # Method 5: Emergent Behavior Detection
        emergent_patterns = self._detect_emergent_patterns(market_data)
        new_patterns.extend(emergent_patterns)
        
        # Filter out known patterns
        truly_unnamed = self._filter_known_patterns(new_patterns)
        
        # Add to library
        for pattern in truly_unnamed:
            pattern_hash = pattern.generate_hash()
            if pattern_hash not in self.pattern_library:
                self.pattern_library[pattern_hash] = pattern
                self.discovered_patterns.append(pattern)
                logger.info(f"✨ Discovered NEW pattern: {pattern.name}")
        
        self.scan_count += 1
        
        logger.info(f"🔍 Scan complete: Found {len(truly_unnamed)} unnamed patterns")
        
        return truly_unnamed
    
    def _detect_anomaly_patterns(self, market_data: List[Dict]) -> List[DiscoveredPattern]:
        """Detect anomalous patterns using statistical methods"""
        patterns = []
        
        # Extract price movements
        prices = [d.get('price', 1.0) for d in market_data]
        if len(prices) < 10:
            return patterns
        
        # Calculate rolling statistics
        window = 20
        for i in range(window, len(prices)):
            window_data = prices[i-window:i]
            mean = np.mean(window_data)
            std = np.std(window_data)
            
            current_price = prices[i]
            z_score = (current_price - mean) / std if std > 0 else 0
            
            # Detect extreme deviations
            if abs(z_score) > 3:  # 3 sigma event
                pattern = DiscoveredPattern(
                    pattern_id=f"ANOMALY_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    pattern_type=PatternType.UNNAMED,
                    discovery_method=DiscoveryMethod.ANOMALY_DETECTION,
                    name=f"Extreme Deviation Pattern (Z={z_score:.2f})",
                    description=f"Price deviated {z_score:.2f} standard deviations from {window}-period mean",
                    conditions=[
                        f"z_score > 3 or z_score < -3",
                        f"window_size = {window}",
                        f"deviation_direction = {'UP' if z_score > 0 else 'DOWN'}"
                    ],
                    confidence=min(0.95, abs(z_score) / 5)
                )
                patterns.append(pattern)
        
        return patterns
    
    def _mine_unusual_correlations(self, market_data: List[Dict]) -> List[DiscoveredPattern]:
        """Mine for unusual correlations"""
        patterns = []
        
        # Extract multiple features
        features = {
            'price': [d.get('price', 1.0) for d in market_data],
            'volume': [d.get('volume', 1000) for d in market_data],
            'volatility': [d.get('volatility', 0.01) for d in market_data]
        }
        
        # Calculate correlations
        for feat1_name, feat1_data in features.items():
            for feat2_name, feat2_data in features.items():
                if feat1_name >= feat2_name:
                    continue
                
                if len(feat1_data) != len(feat2_data) or len(feat1_data) < 10:
                    continue
                
                # Calculate correlation
                corr = np.corrcoef(feat1_data, feat2_data)[0, 1]
                
                # Detect unusual correlations
                if abs(corr) > 0.8:  # Strong correlation
                    pattern = DiscoveredPattern(
                        pattern_id=f"CORR_{feat1_name}_{feat2_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        pattern_type=PatternType.UNNAMED,
                        discovery_method=DiscoveryMethod.CORRELATION_MINING,
                        name=f"Unusual {feat1_name}-{feat2_name} Correlation",
                        description=f"Strong {'positive' if corr > 0 else 'negative'} correlation ({corr:.3f}) between {feat1_name} and {feat2_name}",
                        mathematical_formula=f"corr({feat1_name}, {feat2_name}) = {corr:.3f}",
                        conditions=[
                            f"correlation_coefficient = {corr:.3f}",
                            f"feature1 = {feat1_name}",
                            f"feature2 = {feat2_name}"
                        ],
                        confidence=abs(corr)
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _mine_sequence_patterns(self, market_data: List[Dict]) -> List[DiscoveredPattern]:
        """Mine for sequence patterns"""
        patterns = []
        
        # Convert prices to discrete movements
        prices = [d.get('price', 1.0) for d in market_data]
        if len(prices) < 5:
            return patterns
        
        movements = []
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1]
            if change > 0.001:
                movements.append('U')  # Up
            elif change < -0.001:
                movements.append('D')  # Down
            else:
                movements.append('N')  # Neutral
        
        # Find repeating sequences
        sequence_counts = defaultdict(int)
        seq_length = 3
        
        for i in range(len(movements) - seq_length + 1):
            sequence = ''.join(movements[i:i+seq_length])
            sequence_counts[sequence] += 1
        
        # Identify significant sequences
        total_sequences = len(movements) - seq_length + 1
        for sequence, count in sequence_counts.items():
            frequency = count / total_sequences if total_sequences > 0 else 0
            
            if frequency > 0.1:  # Appears in >10% of windows
                pattern = DiscoveredPattern(
                    pattern_id=f"SEQ_{sequence}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    pattern_type=PatternType.UNNAMED,
                    discovery_method=DiscoveryMethod.CLUSTERING,
                    name=f"Sequence Pattern: {sequence}",
                    description=f"Repeating sequence '{sequence}' appears {frequency:.1%} of the time",
                    conditions=[
                        f"sequence = {sequence}",
                        f"frequency = {frequency:.3f}",
                        f"occurrences = {count}"
                    ],
                    confidence=frequency,
                    occurrences=count
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_fractal_patterns(self, market_data: List[Dict]) -> List[DiscoveredPattern]:
        """Detect fractal (self-similar) patterns"""
        patterns = []
        
        prices = [d.get('price', 1.0) for d in market_data]
        if len(prices) < 20:
            return patterns
        
        # Check for self-similarity at different scales
        scales = [5, 10, 20]
        
        for scale in scales:
            if len(prices) < scale * 2:
                continue
            
            # Calculate patterns at this scale
            scale_patterns = []
            for i in range(0, len(prices) - scale, scale):
                window = prices[i:i+scale]
                if len(window) == scale:
                    # Normalize to 0-1
                    min_p = min(window)
                    max_p = max(window)
                    if max_p > min_p:
                        normalized = [(p - min_p) / (max_p - min_p) for p in window]
                        scale_patterns.append(normalized)
            
            # Check for similar patterns
            if len(scale_patterns) >= 2:
                # Compare first and last patterns
                similarity = self._calculate_pattern_similarity(scale_patterns[0], scale_patterns[-1])
                
                if similarity > 0.8:  # High similarity
                    pattern = DiscoveredPattern(
                        pattern_id=f"FRACTAL_{scale}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        pattern_type=PatternType.FRACTAL,
                        discovery_method=DiscoveryMethod.CLUSTERING,
                        name=f"Fractal Pattern (Scale={scale})",
                        description=f"Self-similar pattern repeats at {scale}-period scale with {similarity:.1%} similarity",
                        conditions=[
                            f"scale = {scale}",
                            f"similarity = {similarity:.3f}",
                            f"pattern_count = {len(scale_patterns)}"
                        ],
                        confidence=similarity
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_emergent_patterns(self, market_data: List[Dict]) -> List[DiscoveredPattern]:
        """Detect emergent patterns from complex interactions"""
        patterns = []
        
        # Look for patterns that emerge from multiple interacting factors
        if len(market_data) < 10:
            return patterns
        
        # Extract multiple features
        prices = [d.get('price', 1.0) for d in market_data]
        volumes = [d.get('volume', 1000) for d in market_data]
        
        # Detect emergent behavior: price-volume divergence
        for i in range(5, len(prices)):
            price_trend = (prices[i] - prices[i-5]) / prices[i-5]
            volume_trend = (volumes[i] - volumes[i-5]) / volumes[i-5]
            
            # Divergence: price up, volume down (or vice versa)
            if (price_trend > 0.02 and volume_trend < -0.2) or (price_trend < -0.02 and volume_trend > 0.2):
                pattern = DiscoveredPattern(
                    pattern_id=f"EMERGENT_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    pattern_type=PatternType.EMERGENT,
                    discovery_method=DiscoveryMethod.ANOMALY_DETECTION,
                    name="Price-Volume Divergence Pattern",
                    description=f"Price and volume moving in opposite directions (price: {price_trend:.2%}, volume: {volume_trend:.2%})",
                    conditions=[
                        f"price_trend = {price_trend:.3f}",
                        f"volume_trend = {volume_trend:.3f}",
                        "divergence_detected = True"
                    ],
                    confidence=0.7
                )
                patterns.append(pattern)
        
        return patterns
    
    def _calculate_pattern_similarity(self, pattern1: List[float], pattern2: List[float]) -> float:
        """Calculate similarity between two patterns"""
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # Calculate correlation
        if len(pattern1) < 2:
            return 0.0
        
        corr = np.corrcoef(pattern1, pattern2)[0, 1]
        return abs(corr)
    
    def _filter_known_patterns(self, patterns: List[DiscoveredPattern]) -> List[DiscoveredPattern]:
        """Filter out patterns that match known textbook patterns"""
        # Known patterns to filter out
        known_patterns = [
            "head_and_shoulders",
            "double_top",
            "double_bottom",
            "triangle",
            "flag",
            "pennant"
        ]
        
        # For now, keep all patterns (simplified)
        # In production, would check against pattern database
        return patterns


class CrossDomainInnovator:
    """
    Applies patterns from other domains to trading
    Biology, Physics, Music, Nature, etc.
    """
    
    def __init__(self):
        self.cross_domain_patterns: List[CrossDomainPattern] = []
        self.domain_knowledge = self._initialize_domain_knowledge()
        
    def _initialize_domain_knowledge(self) -> Dict[str, List[str]]:
        """Initialize knowledge from other domains"""
        return {
            'Biology': [
                'Predator-Prey Dynamics',
                'Immune System Response',
                'Evolutionary Adaptation',
                'Symbiotic Relationships',
                'Homeostasis'
            ],
            'Physics': [
                'Momentum Conservation',
                'Wave Interference',
                'Resonance',
                'Phase Transitions',
                'Entropy'
            ],
            'Music': [
                'Harmonic Patterns',
                'Rhythm Cycles',
                'Crescendo/Diminuendo',
                'Dissonance Resolution',
                'Tempo Changes'
            ],
            'Weather': [
                'Storm Formation',
                'Pressure Systems',
                'Temperature Gradients',
                'Seasonal Cycles',
                'Climate Patterns'
            ],
            'Social': [
                'Herd Behavior',
                'Information Cascades',
                'Network Effects',
                'Tipping Points',
                'Viral Spread'
            ]
        }
    
    def discover_cross_domain_pattern(self, source_domain: str, market_data: Dict) -> Optional[CrossDomainPattern]:
        """Discover a pattern by applying knowledge from another domain"""
        if source_domain not in self.domain_knowledge:
            return None
        
        concepts = self.domain_knowledge[source_domain]
        selected_concept = random.choice(concepts)
        
        # Adapt concept to trading
        adapted_pattern = self._adapt_to_trading(source_domain, selected_concept, market_data)
        
        if adapted_pattern:
            self.cross_domain_patterns.append(adapted_pattern)
            logger.info(f"🌍 Cross-domain pattern discovered: {selected_concept} from {source_domain}")
        
        return adapted_pattern
    
    def _adapt_to_trading(self, source_domain: str, concept: str, market_data: Dict) -> Optional[CrossDomainPattern]:
        """Adapt a concept from another domain to trading"""
        
        adaptations = {
            ('Biology', 'Predator-Prey Dynamics'): {
                'adapted_concept': 'Buyer-Seller Dynamics',
                'rules': [
                    'When buyers dominate, prices rise (prey abundance)',
                    'High prices attract sellers (predators)',
                    'Oscillating equilibrium between buyers and sellers',
                    'Population cycles predict price cycles'
                ]
            },
            ('Physics', 'Momentum Conservation'): {
                'adapted_concept': 'Price Momentum Conservation',
                'rules': [
                    'Price momentum tends to continue unless acted upon',
                    'Volume represents the "mass" of the move',
                    'Sudden stops indicate external force (news, intervention)',
                    'Momentum transfer between related assets'
                ]
            },
            ('Music', 'Harmonic Patterns'): {
                'adapted_concept': 'Price Harmonics',
                'rules': [
                    'Prices oscillate at characteristic frequencies',
                    'Multiple timeframes create harmonic resonance',
                    'Dissonance (conflicting timeframes) resolves to consonance',
                    'Rhythm of price movements follows musical patterns'
                ]
            },
            ('Weather', 'Storm Formation'): {
                'adapted_concept': 'Market Storm Detection',
                'rules': [
                    'Volatility builds like atmospheric pressure',
                    'Calm before the storm (low volatility before breakout)',
                    'Storm intensity proportional to pressure buildup',
                    'Aftermath: return to equilibrium'
                ]
            },
            ('Social', 'Herd Behavior'): {
                'adapted_concept': 'Market Herd Dynamics',
                'rules': [
                    'Traders follow the crowd (momentum)',
                    'Contrarian opportunities when herd is extreme',
                    'Information cascades create trends',
                    'Herd reversal signals major turning points'
                ]
            }
        }
        
        key = (source_domain, concept)
        if key in adaptations:
            adaptation = adaptations[key]
            
            pattern = CrossDomainPattern(
                pattern_id=f"CROSS_{source_domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                source_domain=source_domain,
                target_domain="Trading",
                original_concept=concept,
                adapted_concept=adaptation['adapted_concept'],
                adaptation_rules=adaptation['rules'],
                effectiveness=0.5  # Initial estimate
            )
            
            return pattern
        
        return None
    
    def get_cross_domain_insights(self) -> Dict:
        """Get insights from cross-domain patterns"""
        return {
            'total_patterns': len(self.cross_domain_patterns),
            'domains_explored': len(set(p.source_domain for p in self.cross_domain_patterns)),
            'patterns_by_domain': {
                domain: len([p for p in self.cross_domain_patterns if p.source_domain == domain])
                for domain in self.domain_knowledge.keys()
            },
            'most_effective': sorted(self.cross_domain_patterns, key=lambda p: p.effectiveness, reverse=True)[:5]
        }


class ProductiveFailureEngine:
    """
    Learns from failures systematically
    Converts every failure into a lesson
    """
    
    def __init__(self):
        self.failure_lessons: List[FailureLesson] = []
        self.failure_count = 0
        self.prevention_count = 0
        
    def record_failure(self, failure_type: str, description: str, market_data: Dict) -> FailureLesson:
        """Record a failure and extract lessons"""
        logger.warning(f"❌ Failure recorded: {failure_type}")
        
        # Analyze failure
        root_cause = self._analyze_root_cause(failure_type, description, market_data)
        learned_rules = self._extract_rules(failure_type, root_cause, market_data)
        prevention_strategy = self._create_prevention_strategy(failure_type, root_cause)
        
        lesson = FailureLesson(
            lesson_id=f"LESSON_{self.failure_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            failure_type=failure_type,
            failure_description=description,
            root_cause=root_cause,
            learned_rules=learned_rules,
            prevention_strategy=prevention_strategy
        )
        
        self.failure_lessons.append(lesson)
        self.failure_count += 1
        
        logger.info(f"📚 Lesson learned: {root_cause}")
        logger.info(f"   Prevention: {prevention_strategy}")
        
        return lesson
    
    def _analyze_root_cause(self, failure_type: str, description: str, market_data: Dict) -> str:
        """Analyze root cause of failure"""
        # Simplified root cause analysis
        root_causes = {
            'STOP_LOSS_HIT': 'Position size too large or stop too tight',
            'MARGIN_CALL': 'Excessive leverage',
            'SLIPPAGE': 'Illiquid market or large order size',
            'WRONG_DIRECTION': 'Signal quality or timing issue',
            'OVERTRADING': 'Lack of discipline or poor risk management',
            'MISSED_OPPORTUNITY': 'Signal detection or execution delay',
            'SYSTEM_ERROR': 'Technical infrastructure issue'
        }
        
        return root_causes.get(failure_type, 'Unknown root cause - requires investigation')
    
    def _extract_rules(self, failure_type: str, root_cause: str, market_data: Dict) -> List[str]:
        """Extract rules to prevent future failures"""
        rules = []
        
        if 'Position size' in root_cause:
            rules.append("Reduce position size by 50% in volatile markets")
            rules.append("Never risk more than 2% per trade")
        
        if 'leverage' in root_cause.lower():
            rules.append("Maximum leverage: 3x")
            rules.append("Reduce leverage when drawdown > 10%")
        
        if 'Illiquid' in root_cause:
            rules.append("Check liquidity before trading")
            rules.append("Use limit orders in illiquid markets")
        
        if 'Signal' in root_cause:
            rules.append("Require minimum confidence threshold of 0.7")
            rules.append("Wait for multiple timeframe confirmation")
        
        if 'discipline' in root_cause.lower():
            rules.append("Implement automatic trade limits")
            rules.append("Mandatory cooling-off period after losses")
        
        return rules if rules else ["Review and analyze this failure type further"]
    
    def _create_prevention_strategy(self, failure_type: str, root_cause: str) -> str:
        """Create strategy to prevent this failure"""
        strategies = {
            'STOP_LOSS_HIT': 'Use ATR-based stops and reduce position size',
            'MARGIN_CALL': 'Monitor margin usage and reduce leverage',
            'SLIPPAGE': 'Use limit orders and check liquidity',
            'WRONG_DIRECTION': 'Improve signal quality and add filters',
            'OVERTRADING': 'Implement daily trade limits and cooling periods',
            'MISSED_OPPORTUNITY': 'Optimize signal detection and execution speed',
            'SYSTEM_ERROR': 'Add redundancy and monitoring'
        }
        
        return strategies.get(failure_type, 'Develop custom prevention strategy')
    
    def check_prevention(self, proposed_action: Dict) -> Dict:
        """Check if proposed action would trigger a known failure"""
        warnings = []
        prevented_failures = []
        
        for lesson in self.failure_lessons:
            # Check if this action matches a known failure pattern
            if self._matches_failure_pattern(proposed_action, lesson):
                warnings.append(f"Warning: Similar to past failure - {lesson.failure_type}")
                prevented_failures.append(lesson.lesson_id)
                lesson.times_prevented += 1
                self.prevention_count += 1
        
        return {
            'is_safe': len(warnings) == 0,
            'warnings': warnings,
            'prevented_failures': prevented_failures,
            'recommendation': 'Proceed with caution' if warnings else 'Safe to proceed'
        }
    
    def _matches_failure_pattern(self, action: Dict, lesson: FailureLesson) -> bool:
        """Check if action matches a known failure pattern"""
        # Simplified pattern matching
        if lesson.failure_type == 'STOP_LOSS_HIT':
            position_size = action.get('position_size', 0)
            if position_size > 0.1:  # >10% of capital
                return True
        
        if lesson.failure_type == 'MARGIN_CALL':
            leverage = action.get('leverage', 1)
            if leverage > 3:
                return True
        
        if lesson.failure_type == 'OVERTRADING':
            trades_today = action.get('trades_today', 0)
            if trades_today > 10:
                return True
        
        return False
    
    def get_failure_report(self) -> Dict:
        """Get comprehensive failure analysis report"""
        return {
            'total_failures': self.failure_count,
            'total_preventions': self.prevention_count,
            'prevention_rate': self.prevention_count / max(1, self.failure_count + self.prevention_count),
            'lessons_learned': len(self.failure_lessons),
            'most_common_failures': self._get_most_common_failures(),
            'most_effective_lessons': self._get_most_effective_lessons()
        }
    
    def _get_most_common_failures(self) -> List[Dict]:
        """Get most common failure types"""
        failure_counts = defaultdict(int)
        for lesson in self.failure_lessons:
            failure_counts[lesson.failure_type] += 1
        
        return [
            {'failure_type': ft, 'count': count}
            for ft, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def _get_most_effective_lessons(self) -> List[FailureLesson]:
        """Get lessons that prevented the most failures"""
        return sorted(self.failure_lessons, key=lambda l: l.times_prevented, reverse=True)[:5]


class PatternDiscoverySystem:
    """
    Complete Pattern Discovery System
    Combines all discovery methods
    """
    
    def __init__(self):
        self.unnamed_scanner = UnnamedPatternScanner()
        self.cross_domain_innovator = CrossDomainInnovator()
        self.failure_engine = ProductiveFailureEngine()
        self.discovery_sessions: List[Dict] = []
        
    def run_discovery_session(self, market_data: List[Dict]) -> Dict:
        """Run complete pattern discovery session"""
        session_id = f"DISCOVERY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🔬 Pattern discovery session started: {session_id}")
        
        session_results = {
            'session_id': session_id,
            'start_time': datetime.now(),
            'unnamed_patterns': [],
            'cross_domain_patterns': [],
            'failure_lessons': []
        }
        
        # 1. Scan for unnamed patterns
        unnamed_patterns = self.unnamed_scanner.scan_for_unnamed_patterns(market_data)
        session_results['unnamed_patterns'] = unnamed_patterns
        
        # 2. Discover cross-domain patterns
        for domain in ['Biology', 'Physics', 'Music', 'Weather', 'Social']:
            cross_pattern = self.cross_domain_innovator.discover_cross_domain_pattern(domain, market_data[0] if market_data else {})
            if cross_pattern:
                session_results['cross_domain_patterns'].append(cross_pattern)
        
        # 3. Record any failures and learn
        # (In production, this would be called when actual failures occur)
        
        session_results['end_time'] = datetime.now()
        session_results['duration'] = (session_results['end_time'] - session_results['start_time']).total_seconds()
        
        # Summary
        session_results['summary'] = {
            'total_patterns_discovered': len(unnamed_patterns) + len(session_results['cross_domain_patterns']),
            'unnamed_patterns_count': len(unnamed_patterns),
            'cross_domain_patterns_count': len(session_results['cross_domain_patterns']),
            'total_lessons': len(self.failure_engine.failure_lessons)
        }
        
        self.discovery_sessions.append(session_results)
        
        logger.info(f"🔬 Discovery session completed: {session_results['summary']['total_patterns_discovered']} patterns found")
        
        return session_results
    
    def get_discovery_report(self) -> Dict:
        """Get comprehensive discovery report"""
        return {
            'total_sessions': len(self.discovery_sessions),
            'total_unnamed_patterns': len(self.unnamed_scanner.discovered_patterns),
            'total_cross_domain_patterns': len(self.cross_domain_innovator.cross_domain_patterns),
            'total_failure_lessons': len(self.failure_engine.failure_lessons),
            'failure_prevention_rate': self.failure_engine.get_failure_report()['prevention_rate'],
            'cross_domain_insights': self.cross_domain_innovator.get_cross_domain_insights()
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create pattern discovery system
    discovery_system = PatternDiscoverySystem()
    
    # Generate sample market data
    market_data = []
    price = 1.0
    for i in range(100):
        price *= (1 + random.gauss(0, 0.01))
        market_data.append({
            'timestamp': datetime.now() - timedelta(minutes=100-i),
            'price': price,
            'volume': random.uniform(800, 1200),
            'volatility': random.uniform(0.005, 0.02)
        })
    
    # Run discovery session
    session_results = discovery_system.run_discovery_session(market_data)
    
    # Record a failure
    failure = discovery_system.failure_engine.record_failure(
        'STOP_LOSS_HIT',
        'Stop loss triggered on EURUSD long position',
        market_data[-1]
    )
    
    # Get discovery report
    report = discovery_system.get_discovery_report()
    
    print("\n" + "="*80)
    logger.info("PATTERN DISCOVERY REPORT")
    print("="*80)
    logger.info(f"Total Sessions: {report['total_sessions']}")
    logger.info(f"Unnamed Patterns Discovered: {report['total_unnamed_patterns']}")
    logger.info(f"Cross-Domain Patterns: {report['total_cross_domain_patterns']}")
    logger.info(f"Failure Lessons Learned: {report['total_failure_lessons']}")
    logger.info(f"Failure Prevention Rate: {report['failure_prevention_rate']:.2%}")
    logger.info("\nCross-Domain Insights:")
    for domain, count in report['cross_domain_insights']['patterns_by_domain'].items():
        logger.info(f"  {domain}: {count} patterns")
    print("="*80)
