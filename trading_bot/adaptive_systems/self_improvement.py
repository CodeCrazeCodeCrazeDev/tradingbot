import logging
logger = logging.getLogger(__name__)
"""Self-Improvement Learning System.

This module implements continuous learning and self-improvement capabilities
that allow the trading bot to evolve and enhance its performance over time.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import pickle
import json
import numpy
import pandas


class LearningType(Enum):
    """Types of learning patterns."""
    MISTAKE_PATTERN = "mistake_pattern"
    SUCCESS_PATTERN = "success_pattern"
    MARKET_PATTERN = "market_pattern"
    STRATEGY_PATTERN = "strategy_pattern"
    RISK_PATTERN = "risk_pattern"


class ModificationStatus(Enum):
    """Status of a modification task."""
    PENDING = "pending"
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    SAFETY_CHECK = "safety_check"
    PRINCIPLES_CHECK = "principles_check"
    APPROVAL_PENDING = "approval_pending"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class LearningInsight:
    """A learned insight from trading experience."""
    insight_id: str
    learning_type: LearningType
    pattern: Dict[str, Any]
    confidence: float
    impact_score: float
    discovery_date: datetime
    validation_count: int = 0
    success_rate: float = 0.0
    last_applied: Optional[datetime] = None
    active: bool = True


@dataclass
class PerformancePattern:
    """Pattern in trading performance."""
    conditions: Dict[str, Any]
    outcome: str
    frequency: int
    avg_pnl: float
    confidence: float
    market_regime: Optional[str] = None


class SelfImprovementEngine:
    """Continuous learning and self-improvement system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the self-improvement engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.insights = {}
        self.performance_history = []
        self.mistake_patterns = []
        self.success_patterns = []
        
        # Learning models
        self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
        # Learning parameters
        self.min_pattern_frequency = self.config.get('min_pattern_frequency', 5)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.learning_window = self.config.get('learning_window', 1000)  # trades
        
        # Knowledge base
        self.knowledge_base = {
            'market_conditions': {},
            'strategy_effectiveness': {},
            'risk_scenarios': {},
            'optimization_history': []
        }
        
        logger.info("SelfImprovementEngine initialized")
    
    def learn_from_trade(self, trade_data: Dict[str, Any]):
        """Learn from a completed trade.
        
        Args:
            trade_data: Complete trade information including outcome
        """
        self.performance_history.append(trade_data)
        
        # Keep only recent history
        if len(self.performance_history) > self.learning_window:
            self.performance_history = self.performance_history[-self.learning_window:]
        
        # Analyze for patterns
        if len(self.performance_history) >= self.min_pattern_frequency:
            self._analyze_trade_patterns()
            self._detect_mistakes()
            self._identify_success_factors()
            self._update_knowledge_base(trade_data)
        
        logger.debug(f"Learned from trade: PnL={trade_data.get('pnl', 0):.2f}")
    
    def _analyze_trade_patterns(self):
        """Analyze trading patterns for insights."""
        recent_trades = self.performance_history[-100:]  # Last 100 trades
        
        # Group trades by outcome
        winning_trades = [t for t in recent_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in recent_trades if t.get('pnl', 0) < 0]
        
        # Analyze winning patterns
        if len(winning_trades) >= self.min_pattern_frequency:
            win_patterns = self._extract_patterns(winning_trades, 'success')
            for pattern in win_patterns:
                self._add_insight(pattern, LearningType.SUCCESS_PATTERN)
        
        # Analyze losing patterns
        if len(losing_trades) >= self.min_pattern_frequency:
            loss_patterns = self._extract_patterns(losing_trades, 'mistake')
            for pattern in loss_patterns:
                self._add_insight(pattern, LearningType.MISTAKE_PATTERN)
    
    def _extract_patterns(self, trades: List[Dict], outcome_type: str) -> List[Dict]:
        """Extract common patterns from trades."""
        patterns = []
        
        if not trades:
            return patterns
        
        # Feature extraction
        features = []
        for trade in trades:
            feature_vector = [
                trade.get('entry_confidence', 0.5),
                trade.get('sentiment_score', 0.0),
                trade.get('volatility', 0.02),
                trade.get('trend_strength', 0.0),
                trade.get('risk_reward_ratio', 1.0),
                trade.get('position_size', 0.01),
                trade.get('hold_time_minutes', 60),
                1 if trade.get('regime') == 'trending_bull' else 0,
                1 if trade.get('regime') == 'trending_bear' else 0,
                1 if trade.get('regime') == 'ranging' else 0,
                1 if trade.get('regime') == 'high_volatility' else 0
            ]
            features.append(feature_vector)
        
        # Cluster similar trades
        if len(features) >= 3:
            try:
                clustering = DBSCAN(eps=0.3, min_samples=2)
                clusters = clustering.fit_predict(features)
                
                # Extract patterns from clusters
                for cluster_id in set(clusters):
                    if cluster_id == -1:  # Noise
                        continue
                    
                    cluster_trades = [trades[i] for i, c in enumerate(clusters) if c == cluster_id]
                    if len(cluster_trades) >= self.min_pattern_frequency:
                        pattern = self._create_pattern_from_cluster(cluster_trades, outcome_type)
                        patterns.append(pattern)
                        
            except Exception as e:
                logger.warning(f"Error in pattern clustering: {e}")
        
        return patterns
    
    def _create_pattern_from_cluster(self, trades: List[Dict], outcome_type: str) -> Dict:
        """Create a pattern description from clustered trades."""
        # Calculate averages and ranges
        avg_pnl = np.mean([t.get('pnl', 0) for t in trades])
        avg_confidence = np.mean([t.get('entry_confidence', 0.5) for t in trades])
        avg_sentiment = np.mean([t.get('sentiment_score', 0) for t in trades])
        
        # Most common regime
        regimes = [t.get('regime', 'unknown') for t in trades]
        most_common_regime = max(set(regimes), key=regimes.count)
        
        pattern = {
            'outcome_type': outcome_type,
            'frequency': len(trades),
            'avg_pnl': avg_pnl,
            'conditions': {
                'confidence_range': [avg_confidence - 0.1, avg_confidence + 0.1],
                'sentiment_range': [avg_sentiment - 0.2, avg_sentiment + 0.2],
                'preferred_regime': most_common_regime
            },
            'confidence': min(1.0, len(trades) / 10.0),  # Higher confidence with more samples
            'discovery_date': datetime.now()
        }
        
        return pattern
    
    def _detect_mistakes(self):
        """Detect recurring mistake patterns."""
        losing_trades = [t for t in self.performance_history[-50:] if t.get('pnl', 0) < 0]
        
        if len(losing_trades) < 3:
            return
        
        # Common mistake patterns
        mistake_checks = [
            self._check_overconfidence_mistakes(losing_trades),
            self._check_regime_mismatch_mistakes(losing_trades),
            self._check_risk_management_mistakes(losing_trades),
            self._check_timing_mistakes(losing_trades)
        ]
        
        for mistake_pattern in mistake_checks:
            if mistake_pattern:
                self._add_insight(mistake_pattern, LearningType.MISTAKE_PATTERN)
    
    def _check_overconfidence_mistakes(self, trades: List[Dict]) -> Optional[Dict]:
        """Check for overconfidence-related mistakes."""
        high_confidence_losses = [t for t in trades if t.get('entry_confidence', 0) > 0.8]
        
        if len(high_confidence_losses) >= 3:
            avg_loss = np.mean([t['pnl'] for t in high_confidence_losses])
            return {
                'pattern_type': 'overconfidence',
                'description': 'High confidence trades resulting in losses',
                'frequency': len(high_confidence_losses),
                'avg_impact': avg_loss,
                'recommendation': 'Reduce position size for high confidence trades',
                'confidence': 0.8
            }
        return None
    
    def _check_regime_mismatch_mistakes(self, trades: List[Dict]) -> Optional[Dict]:
        """Check for regime mismatch mistakes."""
        regime_mismatches = []
        for trade in trades:
            strategy = trade.get('strategy', '')
            regime = trade.get('regime', '')
            
            # Check for obvious mismatches
            if (strategy == 'trend_following' and regime == 'ranging') or \
               (strategy == 'mean_reversion' and regime in ['trending_bull', 'trending_bear']):
                regime_mismatches.append(trade)
        
        if len(regime_mismatches) >= 2:
            avg_loss = np.mean([t['pnl'] for t in regime_mismatches])
            return {
                'pattern_type': 'regime_mismatch',
                'description': 'Strategy-regime mismatches causing losses',
                'frequency': len(regime_mismatches),
                'avg_impact': avg_loss,
                'recommendation': 'Improve strategy-regime alignment',
                'confidence': 0.9
            }
        return None
    
    def _check_risk_management_mistakes(self, trades: List[Dict]) -> Optional[Dict]:
        """Check for risk management mistakes."""
        large_losses = [t for t in trades if t.get('pnl', 0) < -0.03]  # > 3% loss
        
        if len(large_losses) >= 2:
            return {
                'pattern_type': 'poor_risk_management',
                'description': 'Excessive losses indicating poor risk control',
                'frequency': len(large_losses),
                'avg_impact': np.mean([t['pnl'] for t in large_losses]),
                'recommendation': 'Tighten stop losses and reduce position sizes',
                'confidence': 0.85
            }
        return None
    
    def _check_timing_mistakes(self, trades: List[Dict]) -> Optional[Dict]:
        """Check for timing-related mistakes."""
        quick_losses = [t for t in trades if t.get('hold_time_minutes', 60) < 15 and t.get('pnl', 0) < 0]
        
        if len(quick_losses) >= 3:
            return {
                'pattern_type': 'poor_timing',
                'description': 'Quick losses suggesting poor entry timing',
                'frequency': len(quick_losses),
                'avg_impact': np.mean([t['pnl'] for t in quick_losses]),
                'recommendation': 'Improve entry timing and confirmation signals',
                'confidence': 0.7
            }
        return None
    
    def _identify_success_factors(self):
        """Identify factors that contribute to success."""
        winning_trades = [t for t in self.performance_history[-50:] if t.get('pnl', 0) > 0]
        
        if len(winning_trades) < 5:
            return
        
        # Analyze success patterns
        success_factors = []
        
        # High sentiment alignment
        high_sentiment_wins = [t for t in winning_trades if abs(t.get('sentiment_score', 0)) > 0.3]
        if len(high_sentiment_wins) >= 3:
            success_factors.append({
                'factor': 'sentiment_alignment',
                'description': 'Strong sentiment alignment improves win rate',
                'frequency': len(high_sentiment_wins),
                'avg_profit': np.mean([t['pnl'] for t in high_sentiment_wins]),
                'confidence': 0.8
            })
        
        # Regime alignment
        for regime in ['trending_bull', 'trending_bear', 'ranging']:
            regime_wins = [t for t in winning_trades if t.get('regime') == regime]
            if len(regime_wins) >= 3:
                success_factors.append({
                    'factor': f'{regime}_success',
                    'description': f'Success pattern in {regime} regime',
                    'frequency': len(regime_wins),
                    'avg_profit': np.mean([t['pnl'] for t in regime_wins]),
                    'confidence': 0.75
                })
        
        for factor in success_factors:
            self._add_insight(factor, LearningType.SUCCESS_PATTERN)
    
    def _add_insight(self, pattern: Dict, learning_type: LearningType):
        """Add a new learning insight."""
        insight_id = f"{learning_type.value}_{len(self.insights)}_{int(datetime.now().timestamp())}"
        
        insight = LearningInsight(
            insight_id=insight_id,
            learning_type=learning_type,
            pattern=pattern,
            confidence=pattern.get('confidence', 0.5),
            impact_score=abs(pattern.get('avg_impact', pattern.get('avg_profit', 0))),
            discovery_date=datetime.now()
        )
        
        self.insights[insight_id] = insight
        logger.info(f"New insight discovered: {learning_type.value} - {pattern.get('description', 'Pattern')}")
    
    def _update_knowledge_base(self, trade_data: Dict[str, Any]):
        """Update the knowledge base with new trade information."""
        regime = trade_data.get('regime', 'unknown')
        strategy = trade_data.get('strategy', 'unknown')
        pnl = trade_data.get('pnl', 0)
        
        # Update market conditions knowledge
        if regime not in self.knowledge_base['market_conditions']:
            self.knowledge_base['market_conditions'][regime] = {
                'trade_count': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'best_strategies': {}
            }
        
        regime_data = self.knowledge_base['market_conditions'][regime]
        regime_data['trade_count'] += 1
        regime_data['total_pnl'] += pnl
        
        # Update strategy effectiveness
        if strategy not in regime_data['best_strategies']:
            regime_data['best_strategies'][strategy] = {'count': 0, 'pnl': 0}
        
        regime_data['best_strategies'][strategy]['count'] += 1
        regime_data['best_strategies'][strategy]['pnl'] += pnl
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Get actionable improvement recommendations."""
        recommendations = []
        
        # Analyze recent insights
        recent_insights = [
            insight for insight in self.insights.values()
            if insight.discovery_date > datetime.now() - timedelta(days=7)
            and insight.confidence > self.confidence_threshold
        ]
        
        # Group by learning type
        mistake_insights = [i for i in recent_insights if i.learning_type == LearningType.MISTAKE_PATTERN]
        success_insights = [i for i in recent_insights if i.learning_type == LearningType.SUCCESS_PATTERN]
        
        # Generate recommendations from mistakes
        for insight in mistake_insights:
            recommendations.append({
                'type': 'fix_mistake',
                'priority': 'high',
                'description': insight.pattern.get('description', 'Unknown mistake pattern'),
                'recommendation': insight.pattern.get('recommendation', 'Review and adjust'),
                'confidence': insight.confidence,
                'impact': insight.impact_score
            })
        
        # Generate recommendations from successes
        for insight in success_insights:
            recommendations.append({
                'type': 'amplify_success',
                'priority': 'medium',
                'description': insight.pattern.get('description', 'Success pattern'),
                'recommendation': f"Increase focus on {insight.pattern.get('factor', 'this pattern')}",
                'confidence': insight.confidence,
                'impact': insight.impact_score
            })
        
        # Sort by impact and confidence
        recommendations.sort(key=lambda x: x['impact'] * x['confidence'], reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def apply_learned_insights(self, current_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Apply learned insights to current trading conditions."""
        adjustments = {}
        
        # Check for applicable insights
        for insight in self.insights.values():
            if not insight.active or insight.confidence < self.confidence_threshold:
                continue
            
            if self._insight_applies(insight, current_conditions):
                adjustment = self._generate_adjustment(insight, current_conditions)
                if adjustment:
                    adjustments.update(adjustment)
                    insight.last_applied = datetime.now()
                    insight.validation_count += 1
        
        return adjustments
    
    def _insight_applies(self, insight: LearningInsight, conditions: Dict[str, Any]) -> bool:
        """Check if an insight applies to current conditions."""
        pattern = insight.pattern
        
        # Check regime match
        if 'preferred_regime' in pattern.get('conditions', {}):
            if conditions.get('regime') != pattern['conditions']['preferred_regime']:
                return False
        
        # Check confidence range
        if 'confidence_range' in pattern.get('conditions', {}):
            conf_range = pattern['conditions']['confidence_range']
            current_conf = conditions.get('confidence', 0.5)
            if not (conf_range[0] <= current_conf <= conf_range[1]):
                return False
        
        return True
    
    def _generate_adjustment(self, insight: LearningInsight, conditions: Dict[str, Any]) -> Optional[Dict]:
        """Generate parameter adjustments based on insight."""
        if insight.learning_type == LearningType.MISTAKE_PATTERN:
            pattern_type = insight.pattern.get('pattern_type')
            
            if pattern_type == 'overconfidence':
                return {'position_size_multiplier': 0.8}
            elif pattern_type == 'poor_risk_management':
                return {'stop_loss_multiplier': 0.8, 'position_size_multiplier': 0.7}
            elif pattern_type == 'poor_timing':
                return {'entry_confidence_threshold': 0.75}
                
        elif insight.learning_type == LearningType.SUCCESS_PATTERN:
            factor = insight.pattern.get('factor')
            
            if 'sentiment_alignment' in factor:
                return {'sentiment_weight_multiplier': 1.2}
            elif 'success' in factor:
                return {'confidence_boost': 0.1}
        
        return None
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary."""
        total_insights = len(self.insights)
        active_insights = len([i for i in self.insights.values() if i.active])
        
        # Count by type
        insight_counts = {}
        for learning_type in LearningType:
            count = len([i for i in self.insights.values() if i.learning_type == learning_type])
            insight_counts[learning_type.value] = count
        
        # Recent performance
        recent_trades = self.performance_history[-50:] if self.performance_history else []
        recent_pnl = sum(t.get('pnl', 0) for t in recent_trades)
        
        return {
            'total_insights': total_insights,
            'active_insights': active_insights,
            'insight_breakdown': insight_counts,
            'recent_performance': recent_pnl,
            'learning_window_size': len(self.performance_history),
            'top_recommendations': self.get_improvement_recommendations()[:3]
        }
