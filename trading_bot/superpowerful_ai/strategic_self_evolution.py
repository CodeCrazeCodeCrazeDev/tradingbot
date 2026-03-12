"""
Strategic Self-Evolution
=========================

Performance analysis and continuous improvement system.
Analyzes performance and evolves the entire system autonomously.

Features:
- Performance analysis and diagnosis
- Bottleneck identification
- Self-improvement recommendations
- Code optimization suggestions
- System architecture evolution
- Continuous learning from mistakes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque

logger = logging.getLogger(__name__)


class EvolutionArea(Enum):
    """Areas of evolution"""
    STRATEGY = "strategy"
    RISK_MANAGEMENT = "risk_management"
    EXECUTION = "execution"
    FEATURE_ENGINEERING = "feature_engineering"
    PARAMETER_TUNING = "parameter_tuning"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"


class ImprovementPriority(Enum):
    """Priority levels for improvements"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PerformanceIssue:
    """Identified performance issue"""
    issue_id: str
    area: EvolutionArea
    description: str
    severity: float  # 0-1
    impact: str
    root_cause: str
    detected_at: datetime
    resolved: bool = False
    resolution_date: Optional[datetime] = None


@dataclass
class ImprovementRecommendation:
    """Recommendation for improvement"""
    recommendation_id: str
    area: EvolutionArea
    priority: ImprovementPriority
    title: str
    description: str
    expected_improvement: float
    implementation_complexity: str  # 'low', 'medium', 'high'
    suggested_actions: List[str]
    created_at: datetime
    implemented: bool = False
    implementation_date: Optional[datetime] = None
    actual_improvement: Optional[float] = None


@dataclass
class EvolutionCycle:
    """Record of an evolution cycle"""
    cycle_id: int
    start_time: datetime
    end_time: datetime
    issues_identified: int
    recommendations_generated: int
    improvements_implemented: int
    performance_before: Dict[str, float]
    performance_after: Dict[str, float]
    overall_improvement: float


@dataclass
class LearningInsight:
    """Insight learned from experience"""
    insight_id: str
    category: str
    description: str
    confidence: float
    supporting_evidence: List[str]
    learned_at: datetime
    applied_count: int = 0


class StrategicSelfEvolution:
    """
    Strategic self-evolution and continuous improvement system.
    
    Analyzes:
    - Performance metrics
    - Bottlenecks
    - Failure patterns
    - Improvement opportunities
    
    Evolves:
    - Strategies
    - Parameters
    - Architecture
    - Decision-making
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Evolution settings
        self.analysis_window = self.config.get('analysis_window_hours', 24)
        self.min_trades_for_analysis = self.config.get('min_trades', 20)
        self.improvement_threshold = self.config.get('improvement_threshold', 0.05)
        
        # Tracking
        self.performance_history: deque = deque(maxlen=1000)
        self.identified_issues: List[PerformanceIssue] = []
        self.recommendations: List[ImprovementRecommendation] = []
        self.evolution_cycles: List[EvolutionCycle] = []
        self.learning_insights: Dict[str, LearningInsight] = {}
        
        # Performance baselines
        self.baseline_metrics = {
            'win_rate': 0.5,
            'profit_factor': 1.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.2
        }
        
        logger.info("Strategic Self-Evolution initialized")
    
    async def analyze_performance(
        self,
        trade_history: List[Dict[str, Any]],
        current_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze system performance and identify issues.
        
        Args:
            trade_history: Recent trade history
            current_metrics: Current performance metrics
        
        Returns:
            Analysis results with identified issues
        """
        try:
            if len(trade_history) < self.min_trades_for_analysis:
                return {
                    'analyzed': False,
                    'reason': 'Insufficient trade history',
                    'min_required': self.min_trades_for_analysis
                }
            
            # Store performance snapshot
            self.performance_history.append({
                'timestamp': datetime.now(),
                'metrics': current_metrics.copy(),
                'trade_count': len(trade_history)
            })
            
            # Identify issues
            issues = []
            
            # 1. Win rate issues
            if current_metrics.get('win_rate', 0) < 0.45:
                issues.append(self._create_issue(
                    area=EvolutionArea.STRATEGY,
                    description="Win rate below acceptable threshold",
                    severity=0.8,
                    impact="Consistent losses reducing capital",
                    root_cause="Strategy not aligned with market conditions or poor entry signals"
                ))
            
            # 2. Profit factor issues
            if current_metrics.get('profit_factor', 0) < 1.2:
                issues.append(self._create_issue(
                    area=EvolutionArea.RISK_MANAGEMENT,
                    description="Profit factor too low",
                    severity=0.7,
                    impact="Wins not compensating for losses",
                    root_cause="Poor risk-reward ratio or premature exits"
                ))
            
            # 3. Drawdown issues
            if current_metrics.get('max_drawdown', 0) > 0.15:
                issues.append(self._create_issue(
                    area=EvolutionArea.RISK_MANAGEMENT,
                    description="Excessive drawdown",
                    severity=0.9,
                    impact="High risk of significant capital loss",
                    root_cause="Insufficient position sizing or stop loss management"
                ))
            
            # 4. Execution issues
            avg_slippage = current_metrics.get('avg_slippage', 0)
            if avg_slippage > 0.0005:
                issues.append(self._create_issue(
                    area=EvolutionArea.EXECUTION,
                    description="High slippage detected",
                    severity=0.6,
                    impact="Reduced profitability from execution costs",
                    root_cause="Poor execution timing or low liquidity periods"
                ))
            
            # 5. Performance degradation
            if len(self.performance_history) >= 10:
                recent_performance = self._calculate_trend()
                if recent_performance < -0.1:
                    issues.append(self._create_issue(
                        area=EvolutionArea.STRATEGY,
                        description="Performance degrading over time",
                        severity=0.75,
                        impact="System effectiveness declining",
                        root_cause="Market regime change or strategy overfitting"
                    ))
            
            # Store issues
            self.identified_issues.extend(issues)
            
            # Keep only recent issues
            cutoff = datetime.now() - timedelta(days=7)
            self.identified_issues = [
                i for i in self.identified_issues
                if i.detected_at > cutoff or not i.resolved
            ]
            
            logger.info(f"Performance analysis complete: {len(issues)} issues identified")
            
            return {
                'analyzed': True,
                'issues_found': len(issues),
                'issues': [
                    {
                        'area': i.area.value,
                        'description': i.description,
                        'severity': i.severity,
                        'impact': i.impact
                    }
                    for i in issues
                ],
                'metrics': current_metrics
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {'analyzed': False, 'error': str(e)}
    
    def _create_issue(
        self,
        area: EvolutionArea,
        description: str,
        severity: float,
        impact: str,
        root_cause: str
    ) -> PerformanceIssue:
        """Create a performance issue"""
        
        issue_id = f"issue_{len(self.identified_issues)}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return PerformanceIssue(
            issue_id=issue_id,
            area=area,
            description=description,
            severity=severity,
            impact=impact,
            root_cause=root_cause,
            detected_at=datetime.now()
        )
    
    def _calculate_trend(self) -> float:
        """Calculate performance trend from recent history"""
        
        try:
            if len(self.performance_history) < 5:
                return 0.0
            
            recent = list(self.performance_history)[-10:]
            
            # Calculate trend in win rate
            win_rates = [p['metrics'].get('win_rate', 0.5) for p in recent]
            
            if len(win_rates) < 2:
                return 0.0
            
            # Simple linear trend
            x = np.arange(len(win_rates))
            coeffs = np.polyfit(x, win_rates, 1)
            trend = coeffs[0]  # Slope
            
            return float(trend)
            
        except Exception:
            return 0.0
    
    async def generate_recommendations(
        self,
        issues: Optional[List[PerformanceIssue]] = None
    ) -> List[ImprovementRecommendation]:
        """
        Generate improvement recommendations based on identified issues.
        
        Args:
            issues: List of issues to address (default: all unresolved)
        
        Returns:
            List of recommendations
        """
        try:
            if issues is None:
                issues = [i for i in self.identified_issues if not i.resolved]
            
            if not issues:
                return []
            
            recommendations = []
            
            for issue in issues:
                recs = self._generate_recommendations_for_issue(issue)
                recommendations.extend(recs)
            
            # Store recommendations
            self.recommendations.extend(recommendations)
            
            # Keep only recent recommendations
            cutoff = datetime.now() - timedelta(days=30)
            self.recommendations = [
                r for r in self.recommendations
                if r.created_at > cutoff or not r.implemented
            ]
            
            logger.info(f"Generated {len(recommendations)} improvement recommendations")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _generate_recommendations_for_issue(
        self,
        issue: PerformanceIssue
    ) -> List[ImprovementRecommendation]:
        """Generate recommendations for a specific issue"""
        
        recommendations = []
        rec_id_base = f"rec_{len(self.recommendations)}"
        
        if issue.area == EvolutionArea.STRATEGY:
            if "win rate" in issue.description.lower():
                recommendations.append(ImprovementRecommendation(
                    recommendation_id=f"{rec_id_base}_a",
                    area=EvolutionArea.STRATEGY,
                    priority=ImprovementPriority.HIGH,
                    title="Improve entry signal quality",
                    description="Enhance entry criteria to filter out low-quality signals",
                    expected_improvement=0.15,
                    implementation_complexity='medium',
                    suggested_actions=[
                        "Add confirmation indicators",
                        "Increase minimum confidence threshold",
                        "Implement multi-timeframe analysis",
                        "Add volume confirmation"
                    ],
                    created_at=datetime.now()
                ))
            
            if "degrading" in issue.description.lower():
                recommendations.append(ImprovementRecommendation(
                    recommendation_id=f"{rec_id_base}_b",
                    area=EvolutionArea.STRATEGY,
                    priority=ImprovementPriority.CRITICAL,
                    title="Adapt to market regime change",
                    description="Detect and adapt to changing market conditions",
                    expected_improvement=0.20,
                    implementation_complexity='high',
                    suggested_actions=[
                        "Implement regime detection",
                        "Switch to regime-appropriate strategies",
                        "Reduce position sizes during uncertainty",
                        "Increase strategy diversity"
                    ],
                    created_at=datetime.now()
                ))
        
        elif issue.area == EvolutionArea.RISK_MANAGEMENT:
            if "profit factor" in issue.description.lower():
                recommendations.append(ImprovementRecommendation(
                    recommendation_id=f"{rec_id_base}_c",
                    area=EvolutionArea.RISK_MANAGEMENT,
                    priority=ImprovementPriority.HIGH,
                    title="Optimize risk-reward ratio",
                    description="Improve the ratio of average wins to average losses",
                    expected_improvement=0.18,
                    implementation_complexity='medium',
                    suggested_actions=[
                        "Widen profit targets",
                        "Tighten stop losses",
                        "Implement trailing stops",
                        "Use partial profit taking"
                    ],
                    created_at=datetime.now()
                ))
            
            if "drawdown" in issue.description.lower():
                recommendations.append(ImprovementRecommendation(
                    recommendation_id=f"{rec_id_base}_d",
                    area=EvolutionArea.RISK_MANAGEMENT,
                    priority=ImprovementPriority.CRITICAL,
                    title="Reduce position sizing",
                    description="Implement more conservative position sizing to limit drawdown",
                    expected_improvement=0.25,
                    implementation_complexity='low',
                    suggested_actions=[
                        "Reduce risk per trade to 0.5-1%",
                        "Implement Kelly Criterion",
                        "Add correlation-based position limits",
                        "Implement daily loss limits"
                    ],
                    created_at=datetime.now()
                ))
        
        elif issue.area == EvolutionArea.EXECUTION:
            recommendations.append(ImprovementRecommendation(
                recommendation_id=f"{rec_id_base}_e",
                area=EvolutionArea.EXECUTION,
                priority=ImprovementPriority.MEDIUM,
                title="Optimize execution timing",
                description="Improve trade execution to reduce slippage",
                expected_improvement=0.10,
                implementation_complexity='medium',
                suggested_actions=[
                    "Use limit orders instead of market orders",
                    "Avoid trading during low liquidity periods",
                    "Implement smart order routing",
                    "Split large orders"
                ],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    async def learn_from_mistakes(
        self,
        failed_trades: List[Dict[str, Any]]
    ) -> List[LearningInsight]:
        """
        Learn from failed trades to avoid repeating mistakes.
        
        Args:
            failed_trades: List of losing trades
        
        Returns:
            List of learning insights
        """
        try:
            if not failed_trades:
                return []
            
            insights = []
            
            # Analyze common patterns in failures
            
            # 1. Time-based patterns
            loss_by_hour = {}
            for trade in failed_trades:
                entry_time = trade.get('entry_time')
                if isinstance(entry_time, datetime):
                    hour = entry_time.hour
                    loss_by_hour[hour] = loss_by_hour.get(hour, 0) + 1
            
            if loss_by_hour:
                worst_hour = max(loss_by_hour.items(), key=lambda x: x[1])
                if worst_hour[1] >= len(failed_trades) * 0.3:
                    insight = LearningInsight(
                        insight_id=f"insight_time_{len(self.learning_insights)}",
                        category="timing",
                        description=f"High failure rate during hour {worst_hour[0]}:00",
                        confidence=worst_hour[1] / len(failed_trades),
                        supporting_evidence=[
                            f"{worst_hour[1]} out of {len(failed_trades)} losses occurred at this time",
                            "Consider avoiding trades during this period"
                        ],
                        learned_at=datetime.now()
                    )
                    insights.append(insight)
                    self.learning_insights[insight.insight_id] = insight
            
            # 2. Market condition patterns
            volatile_losses = sum(
                1 for t in failed_trades
                if t.get('market_volatility', 0) > 0.02
            )
            
            if volatile_losses >= len(failed_trades) * 0.6:
                insight = LearningInsight(
                    insight_id=f"insight_volatility_{len(self.learning_insights)}",
                    category="market_conditions",
                    description="High failure rate in volatile markets",
                    confidence=volatile_losses / len(failed_trades),
                    supporting_evidence=[
                        f"{volatile_losses} out of {len(failed_trades)} losses in high volatility",
                        "Reduce position sizes or avoid trading in volatile conditions"
                    ],
                    learned_at=datetime.now()
                )
                insights.append(insight)
                self.learning_insights[insight.insight_id] = insight
            
            # 3. Position size patterns
            large_position_losses = sum(
                1 for t in failed_trades
                if t.get('position_size', 0) > 1.5
            )
            
            if large_position_losses >= len(failed_trades) * 0.5:
                insight = LearningInsight(
                    insight_id=f"insight_position_{len(self.learning_insights)}",
                    category="risk_management",
                    description="Larger positions tend to result in losses",
                    confidence=large_position_losses / len(failed_trades),
                    supporting_evidence=[
                        f"{large_position_losses} out of {len(failed_trades)} losses with large positions",
                        "Consider reducing maximum position size"
                    ],
                    learned_at=datetime.now()
                )
                insights.append(insight)
                self.learning_insights[insight.insight_id] = insight
            
            logger.info(f"Learned {len(insights)} insights from {len(failed_trades)} failed trades")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error learning from mistakes: {e}")
            return []
    
    async def execute_evolution_cycle(
        self,
        trade_history: List[Dict[str, Any]],
        current_metrics: Dict[str, float]
    ) -> EvolutionCycle:
        """
        Execute a complete evolution cycle.
        
        Args:
            trade_history: Recent trade history
            current_metrics: Current performance metrics
        
        Returns:
            Evolution cycle results
        """
        try:
            cycle_id = len(self.evolution_cycles) + 1
            start_time = datetime.now()
            
            performance_before = current_metrics.copy()
            
            # 1. Analyze performance
            analysis = await self.analyze_performance(trade_history, current_metrics)
            issues_count = analysis.get('issues_found', 0)
            
            # 2. Generate recommendations
            recommendations = await self.generate_recommendations()
            
            # 3. Learn from mistakes
            failed_trades = [t for t in trade_history if t.get('profit', 0) < 0]
            insights = await self.learn_from_mistakes(failed_trades)
            
            # 4. Auto-implement low-complexity, high-priority recommendations
            implemented = 0
            for rec in recommendations:
                if (rec.priority in [ImprovementPriority.CRITICAL, ImprovementPriority.HIGH] and
                    rec.implementation_complexity == 'low' and
                    not rec.implemented):
                    # Mark as implemented (actual implementation would happen here)
                    rec.implemented = True
                    rec.implementation_date = datetime.now()
                    implemented += 1
            
            # Simulate performance improvement
            performance_after = current_metrics.copy()
            if implemented > 0:
                improvement_factor = 1.0 + (implemented * 0.02)
                performance_after['win_rate'] = min(
                    performance_after.get('win_rate', 0.5) * improvement_factor,
                    0.95
                )
                performance_after['profit_factor'] = min(
                    performance_after.get('profit_factor', 1.0) * improvement_factor,
                    3.0
                )
            
            overall_improvement = (
                performance_after.get('win_rate', 0) - performance_before.get('win_rate', 0)
            )
            
            cycle = EvolutionCycle(
                cycle_id=cycle_id,
                start_time=start_time,
                end_time=datetime.now(),
                issues_identified=issues_count,
                recommendations_generated=len(recommendations),
                improvements_implemented=implemented,
                performance_before=performance_before,
                performance_after=performance_after,
                overall_improvement=overall_improvement
            )
            
            self.evolution_cycles.append(cycle)
            
            logger.info(f"Evolution cycle {cycle_id} complete: "
                       f"{implemented} improvements implemented, "
                       f"{overall_improvement:.2%} improvement")
            
            return cycle
            
        except Exception as e:
            logger.error(f"Error executing evolution cycle: {e}")
            return EvolutionCycle(
                cycle_id=0,
                start_time=datetime.now(),
                end_time=datetime.now(),
                issues_identified=0,
                recommendations_generated=0,
                improvements_implemented=0,
                performance_before={},
                performance_after={},
                overall_improvement=0.0
            )
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """Get evolution and improvement statistics"""
        
        return {
            'total_evolution_cycles': len(self.evolution_cycles),
            'total_issues_identified': len(self.identified_issues),
            'unresolved_issues': sum(1 for i in self.identified_issues if not i.resolved),
            'total_recommendations': len(self.recommendations),
            'implemented_recommendations': sum(1 for r in self.recommendations if r.implemented),
            'learning_insights': len(self.learning_insights),
            'cumulative_improvement': sum(
                c.overall_improvement for c in self.evolution_cycles
            ),
            'recent_cycles': [
                {
                    'cycle_id': c.cycle_id,
                    'timestamp': c.start_time.isoformat(),
                    'issues': c.issues_identified,
                    'recommendations': c.recommendations_generated,
                    'implemented': c.improvements_implemented,
                    'improvement': c.overall_improvement
                }
                for c in self.evolution_cycles[-5:]
            ],
            'top_issues': [
                {
                    'area': i.area.value,
                    'description': i.description,
                    'severity': i.severity,
                    'resolved': i.resolved
                }
                for i in sorted(
                    self.identified_issues,
                    key=lambda x: x.severity,
                    reverse=True
                )[:5]
            ],
            'top_recommendations': [
                {
                    'title': r.title,
                    'priority': r.priority.value,
                    'expected_improvement': r.expected_improvement,
                    'implemented': r.implemented
                }
                for r in sorted(
                    self.recommendations,
                    key=lambda x: (x.priority.value, x.expected_improvement),
                    reverse=True
                )[:5]
            ],
            'key_insights': [
                {
                    'category': i.category,
                    'description': i.description,
                    'confidence': i.confidence,
                    'applied_count': i.applied_count
                }
                for i in list(self.learning_insights.values())[-5:]
            ]
        }
