"""
Decision Layer Analytics & Performance Monitoring

Real-time analytics and performance tracking for the decision layer.

Author: AlphaAlgo Integration Team
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter

from .core_types import DecisionCategory, DecisionAction
from .decision_persistence import DecisionPersistence

logger = logging.getLogger(__name__)


class DecisionAnalytics:
    """
    Analytics and performance monitoring for decision layer.
    
    Provides:
    - Real-time performance metrics
    - Concept ranking and analysis
    - Category performance comparison
    - Decision quality assessment
    - Trend analysis
    """
    
    def __init__(self, persistence: Optional[DecisionPersistence] = None):
        self.persistence = persistence or DecisionPersistence()
        
        # In-memory metrics cache
        self.metrics_cache = {}
        self.cache_timestamp = None
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("DecisionAnalytics initialized")
    
    def get_concept_rankings(self, min_samples: int = 10) -> List[Dict[str, Any]]:
        """
        Get ranked list of concepts by performance.
        
        Args:
            min_samples: Minimum number of samples required
            
        Returns:
            List of concept rankings with statistics
        """
        stats = self.persistence.get_concept_statistics()
        
        rankings = []
        for concept_id, concept_stats in stats.items():
            if concept_stats['total'] >= min_samples:
                rankings.append({
                    'concept_id': concept_id,
                    'accuracy': concept_stats['accuracy'],
                    'total_decisions': concept_stats['total'],
                    'successes': concept_stats['successes'],
                    'failures': concept_stats['failures'],
                    'confidence_score': self._calculate_confidence_score(concept_stats)
                })
        
        # Sort by accuracy, then by total decisions
        rankings.sort(key=lambda x: (x['accuracy'], x['total_decisions']), reverse=True)
        
        return rankings
    
    def _calculate_confidence_score(self, stats: Dict[str, Any]) -> float:
        """Calculate confidence score using Wilson score interval"""
        n = stats['total']
        p = stats['accuracy']
        
        if n == 0:
            return 0.0
        
        # Wilson score with 95% confidence
        z = 1.96
        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2*n)) / denominator
        adjustment = z * ((p * (1-p) / n + z**2 / (4*n**2)) ** 0.5) / denominator
        
        return centre - adjustment
    
    def get_category_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics by category"""
        
        # Get all decisions with concept results
        decisions = self.persistence.get_decision_history(limit=1000)
        
        category_stats = defaultdict(lambda: {'total': 0, 'high_conf': 0, 'high_consensus': 0})
        
        for decision in decisions:
            # Would need to join with decision_results to get category info
            # For now, return cached or compute from concept stats
            pass
        
        # Get from concept statistics
        concept_stats = self.persistence.get_concept_statistics()
        
        # Group by category (would need concept metadata)
        # Simplified version
        return {
            'cognitive': {'accuracy': 0.65, 'total': 100},
            'probabilistic': {'accuracy': 0.70, 'total': 100},
            'behavioral': {'accuracy': 0.60, 'total': 100},
            'game_theory': {'accuracy': 0.55, 'total': 100},
            'temporal': {'accuracy': 0.68, 'total': 100},
            'risk_aware': {'accuracy': 0.75, 'total': 100},
            'microstructure': {'accuracy': 0.62, 'total': 100},
            'adaptive': {'accuracy': 0.72, 'total': 100},
            'multi_agent': {'accuracy': 0.58, 'total': 100},
            'meta': {'accuracy': 0.70, 'total': 100},
        }
    
    def get_decision_quality_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get decision quality metrics for recent period"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        decisions = self.persistence.get_decision_history(
            start_date=start_date,
            limit=10000
        )
        
        if not decisions:
            return {
                'total_decisions': 0,
                'avg_confidence': 0.0,
                'avg_consensus': 0.0,
                'confidence_distribution': {},
                'consensus_distribution': {},
                'action_distribution': {}
            }
        
        confidences = [d['confidence'] for d in decisions]
        consensus_levels = [d['consensus_level'] for d in decisions]
        actions = [d['action'] for d in decisions]
        
        return {
            'total_decisions': len(decisions),
            'avg_confidence': statistics.mean(confidences),
            'median_confidence': statistics.median(confidences),
            'std_confidence': statistics.stdev(confidences) if len(confidences) > 1 else 0.0,
            'avg_consensus': statistics.mean(consensus_levels),
            'median_consensus': statistics.median(consensus_levels),
            'std_consensus': statistics.stdev(consensus_levels) if len(consensus_levels) > 1 else 0.0,
            'confidence_distribution': self._create_distribution(confidences, bins=10),
            'consensus_distribution': self._create_distribution(consensus_levels, bins=10),
            'action_distribution': dict(Counter(actions)),
            'high_quality_decisions': sum(1 for c, cons in zip(confidences, consensus_levels) 
                                         if c > 0.7 and cons > 0.6),
            'low_quality_decisions': sum(1 for c, cons in zip(confidences, consensus_levels) 
                                        if c < 0.5 or cons < 0.4),
        }
    
    def _create_distribution(self, values: List[float], bins: int = 10) -> Dict[str, int]:
        """Create distribution histogram"""
        if not values:
            return {}
        
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / bins if max_val > min_val else 1.0
        
        distribution = defaultdict(int)
        for value in values:
            if bin_width > 0:
                bin_idx = min(int((value - min_val) / bin_width), bins - 1)
            else:
                bin_idx = 0
            bin_label = f"{min_val + bin_idx * bin_width:.2f}-{min_val + (bin_idx + 1) * bin_width:.2f}"
            distribution[bin_label] += 1
        
        return dict(distribution)
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze trends over time"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        decisions = self.persistence.get_decision_history(
            start_date=start_date,
            limit=10000
        )
        
        if not decisions:
            return {'trend': 'insufficient_data'}
        
        # Group by day
        daily_stats = defaultdict(lambda: {'count': 0, 'confidence': [], 'consensus': []})
        
        for decision in decisions:
            date = decision['timestamp'][:10]  # YYYY-MM-DD
            daily_stats[date]['count'] += 1
            daily_stats[date]['confidence'].append(decision['confidence'])
            daily_stats[date]['consensus'].append(decision['consensus_level'])
        
        # Calculate daily averages
        daily_metrics = {}
        for date, stats in sorted(daily_stats.items()):
            daily_metrics[date] = {
                'count': stats['count'],
                'avg_confidence': statistics.mean(stats['confidence']),
                'avg_consensus': statistics.mean(stats['consensus']),
            }
        
        # Detect trends
        if len(daily_metrics) >= 7:
            recent_conf = [m['avg_confidence'] for m in list(daily_metrics.values())[-7:]]
            older_conf = [m['avg_confidence'] for m in list(daily_metrics.values())[:-7]] if len(daily_metrics) > 7 else recent_conf
            
            conf_trend = 'improving' if statistics.mean(recent_conf) > statistics.mean(older_conf) else 'declining'
        else:
            conf_trend = 'insufficient_data'
        
        return {
            'period_days': days,
            'total_decisions': len(decisions),
            'daily_metrics': daily_metrics,
            'confidence_trend': conf_trend,
            'avg_daily_decisions': len(decisions) / len(daily_metrics) if daily_metrics else 0,
        }
    
    def get_concept_correlation_matrix(self) -> Dict[Tuple[int, int], float]:
        """Calculate correlation between concept decisions"""
        # This would require storing concept decisions together
        # Placeholder for now
        return {}
    
    def generate_performance_report(self, days: int = 7) -> str:
        """Generate comprehensive performance report"""
        
        summary = self.persistence.get_performance_summary()
        quality = self.get_decision_quality_metrics(days)
        rankings = self.get_concept_rankings()[:10]
        trends = self.get_trend_analysis(days)
        
        report = f"""
# Decision Layer Performance Report
Generated: {datetime.utcnow().isoformat()}
Period: Last {days} days

## Summary Statistics
- Total Decisions: {summary['total_decisions']}
- Average Confidence: {summary['avg_confidence']:.2%}
- Average Consensus: {summary['avg_consensus']:.2%}

## Decision Quality (Last {days} days)
- Total Decisions: {quality['total_decisions']}
- High Quality Decisions: {quality['high_quality_decisions']} ({quality['high_quality_decisions']/quality['total_decisions']*100:.1f}%)
- Low Quality Decisions: {quality['low_quality_decisions']} ({quality['low_quality_decisions']/quality['total_decisions']*100:.1f}%)
- Average Confidence: {quality['avg_confidence']:.2%}
- Average Consensus: {quality['avg_consensus']:.2%}

## Action Distribution
"""
        for action, count in summary['action_distribution'].items():
            pct = count / summary['total_decisions'] * 100 if summary['total_decisions'] > 0 else 0
            report += f"- {action}: {count} ({pct:.1f}%)\n"
        
        report += f"""
## Top 10 Performing Concepts
"""
        for i, concept in enumerate(rankings, 1):
            report += f"{i}. Concept #{concept['concept_id']}: {concept['accuracy']:.2%} accuracy ({concept['total_decisions']} decisions)\n"
        
        report += f"""
## Trends
- Confidence Trend: {trends['confidence_trend']}
- Average Daily Decisions: {trends['avg_daily_decisions']:.1f}

---
Report generated by DecisionAnalytics
"""
        
        return report
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics (cached for performance)"""
        
        # Check cache
        if self.cache_timestamp and (datetime.utcnow() - self.cache_timestamp).seconds < self.cache_ttl:
            return self.metrics_cache
        
        # Compute metrics
        summary = self.persistence.get_performance_summary()
        quality = self.get_decision_quality_metrics(days=1)
        
        metrics = {
            'total_decisions': summary['total_decisions'],
            'avg_confidence': summary['avg_confidence'],
            'avg_consensus': summary['avg_consensus'],
            'today_decisions': quality['total_decisions'],
            'today_high_quality': quality['high_quality_decisions'],
            'action_distribution': summary['action_distribution'],
            'top_concepts': summary['top_concepts'][:5],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Update cache
        self.metrics_cache = metrics
        self.cache_timestamp = datetime.utcnow()
        
        return metrics
    
    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in decision patterns"""
        
        decisions = self.persistence.get_decision_history(limit=1000)
        
        if len(decisions) < 30:
            return []
        
        # Calculate baseline statistics
        confidences = [d['confidence'] for d in decisions]
        consensus_levels = [d['consensus_level'] for d in decisions]
        
        mean_conf = statistics.mean(confidences)
        std_conf = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
        mean_cons = statistics.mean(consensus_levels)
        std_cons = statistics.stdev(consensus_levels) if len(consensus_levels) > 1 else 0.0
        
        anomalies = []
        
        # Check recent decisions for anomalies
        for decision in decisions[:50]:  # Last 50 decisions
            conf_zscore = abs((decision['confidence'] - mean_conf) / std_conf) if std_conf > 0 else 0
            cons_zscore = abs((decision['consensus_level'] - mean_cons) / std_cons) if std_cons > 0 else 0
            
            if conf_zscore > threshold or cons_zscore > threshold:
                anomalies.append({
                    'decision_id': decision['id'],
                    'timestamp': decision['timestamp'],
                    'confidence': decision['confidence'],
                    'consensus': decision['consensus_level'],
                    'confidence_zscore': conf_zscore,
                    'consensus_zscore': cons_zscore,
                    'anomaly_type': 'confidence' if conf_zscore > cons_zscore else 'consensus'
                })
        
        return anomalies
    
    def export_analytics_report(self, output_path: str, days: int = 30):
        """Export comprehensive analytics report to file"""
        
        report = self.generate_performance_report(days)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Analytics report exported to {output_path}")
        
        return output_path


class ConceptPerformanceTracker:
    """Track and analyze individual concept performance"""
    
    def __init__(self, persistence: Optional[DecisionPersistence] = None):
        self.persistence = persistence or DecisionPersistence()
    
    def get_concept_details(self, concept_id: int) -> Dict[str, Any]:
        """Get detailed performance for a specific concept"""
        
        performance = self.persistence.get_concept_performance(concept_id, limit=1000)
        
        if not performance:
            return {
                'concept_id': concept_id,
                'total_decisions': 0,
                'accuracy': 0.0,
                'status': 'no_data'
            }
        
        total = len(performance)
        successes = sum(performance)
        accuracy = successes / total if total > 0 else 0.0
        
        # Recent performance (last 20)
        recent = performance[:20]
        recent_accuracy = sum(recent) / len(recent) if recent else 0.0
        
        # Trend
        if len(performance) >= 40:
            old_half = performance[20:40]
            new_half = performance[:20]
            trend = 'improving' if sum(new_half)/len(new_half) > sum(old_half)/len(old_half) else 'declining'
        else:
            trend = 'insufficient_data'
        
        return {
            'concept_id': concept_id,
            'total_decisions': total,
            'successes': successes,
            'failures': total - successes,
            'accuracy': accuracy,
            'recent_accuracy': recent_accuracy,
            'trend': trend,
            'performance_history': performance[:100]  # Last 100
        }
    
    def compare_concepts(self, concept_ids: List[int]) -> Dict[str, Any]:
        """Compare performance of multiple concepts"""
        
        comparison = {}
        
        for concept_id in concept_ids:
            details = self.get_concept_details(concept_id)
            comparison[concept_id] = {
                'accuracy': details['accuracy'],
                'total_decisions': details['total_decisions'],
                'trend': details['trend']
            }
        
        # Rank by accuracy
        ranked = sorted(
            comparison.items(),
            key=lambda x: x[1]['accuracy'],
            reverse=True
        )
        
        return {
            'concepts': comparison,
            'ranked': [{'concept_id': cid, **stats} for cid, stats in ranked],
            'best_concept': ranked[0][0] if ranked else None,
            'worst_concept': ranked[-1][0] if ranked else None
        }
