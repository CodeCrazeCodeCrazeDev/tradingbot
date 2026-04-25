"""
Experiment Analyzer - ASI-Evolve Complex Outcome Distillation
================================================

Distills complex experimental outputs into actionable insights for future iterations.
Handles multi-dimensional feedback and converts it into structured knowledge.

Based on ASI-Evolve paper: "receives the current program together with the full experimental output—including multiple metrics, feature importances, training logs, and execution traces—and distills them into a compact, decision-oriented report"
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """Structured analysis report from experiment outcomes"""
    validation_passed: bool
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    improvement_suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'validation_passed': self.validation_passed,
            'key_insights': self.key_insights,
            'recommendations': self.recommendations,
            'confidence_score': self.confidence_score,
            'performance_summary': self.performance_summary,
            'improvement_suggestions': self.improvement_suggestions,
            'created_at': self.created_at.isoformat(),
        }


class ExperimentAnalyzer:
    """
    ASI-Evolve Analyzer component for complex outcome distillation.
    
    Processes raw experimental outputs and extracts actionable insights.
    """
    
    def __init__(self):
        self.analysis_history: List[AnalysisReport] = []
        logger.info("Experiment Analyzer initialized")
    
    def initialize(self):
        """Initialize analyzer with domain-specific knowledge"""
        # Domain-specific analysis patterns
        self.analysis_patterns = {
            'trading_strategy': {
                'key_metrics': ['sharpe_ratio', 'max_drawdown', 'win_rate', 'profit_factor'],
                'success_thresholds': {'sharpe_ratio': 1.0, 'win_rate': 0.5},
                'insight_patterns': [
                    'High sharpe with low drawdown indicates effective risk management',
                    'Consistent win rate above 0.5 suggests robust strategy',
                    'Profit factor > 1.5 indicates strong alpha generation'
                ]
            },
            'ml_architecture': {
                'key_metrics': ['accuracy', 'f1_score', 'auc_roc', 'training_time', 'inference_time'],
                'success_thresholds': {'accuracy': 0.8, 'f1_score': 0.75},
                'insight_patterns': [
                    'Low inference time with high accuracy suggests efficient architecture',
                    'High training time may indicate overfitting risk',
                    'AUC-ROC > 0.85 indicates strong discriminative power'
                ]
            },
            'data_curation': {
                'key_metrics': ['data_quality', 'completeness', 'coverage', 'improvement_score'],
                'success_thresholds': {'data_quality': 0.8, 'completeness': 0.9},
                'insight_patterns': [
                    'High completeness with low quality suggests aggressive cleaning',
                    'Poor coverage in specific domains indicates need for targeted curation',
                    'Consistent improvement across iterations shows effective learning'
                ]
            }
        }
    
    async def analyze_outcome(self, program: str, results: Dict[str, Any], 
                          context: Optional[str] = None) -> AnalysisReport:
        """Analyze experimental outcome and generate insights"""
        await asyncio.sleep(0.1)  # Simulate analysis computation
        
        # Determine domain from context or program type
        domain = self._infer_domain(program, context)
        patterns = self.analysis_patterns.get(domain, self.analysis_patterns['general'])
        
        # Extract key insights based on domain patterns
        key_insights = []
        recommendations = []
        validation_passed = True
        confidence_score = 0.7
        
        # Domain-specific analysis logic
        if domain == 'trading_strategy':
            key_insights, recommendations, validation_passed = self._analyze_trading_strategy(results, patterns)
            confidence_score = 0.8 if validation_passed else 0.4
        elif domain == 'ml_architecture':
            key_insights, recommendations, validation_passed = self._analyze_ml_architecture(results, patterns)
            confidence_score = 0.9 if validation_passed else 0.5
        elif domain == 'data_curation':
            key_insights, recommendations, validation_passed = self._analyze_data_curation(results, patterns)
            confidence_score = 0.85 if validation_passed else 0.6
        else:
            # Generic analysis
            key_insights = ['Complex multi-dimensional outcome detected', 'Multiple metrics show conflicting trends']
            recommendations = ['Investigate individual metric components', 'Consider multi-objective optimization']
            confidence_score = 0.6
        
        # Create performance summary
        performance_summary = {
            'primary_score': results.get('score', 0.0),
            'secondary_metrics': {k: v for k, v in results.items() if k != 'score'},
            'trend_analysis': self._analyze_trends(results),
        }
        
        report = AnalysisReport(
            validation_passed=validation_passed,
            key_insights=key_insights,
            recommendations=recommendations,
            confidence_score=confidence_score,
            performance_summary=performance_summary,
        )
        
        self.analysis_history.append(report)
        logger.info(f"Analysis completed with confidence score: {confidence_score}")
        
        return report
    
    def _infer_domain(self, program: str, context: Optional[str]) -> str:
        """Infer domain from program content and context"""
        program_lower = program.lower()
        
        if any(keyword in program_lower for keyword in ['sharpe', 'drawdown', 'portfolio', 'risk', 'strategy']):
            return 'trading_strategy'
        elif any(keyword in program_lower for keyword in ['accuracy', 'model', 'architecture', 'neural', 'transformer', 'attention']):
            return 'ml_architecture'
        elif any(keyword in program_lower for keyword in ['data', 'quality', 'curation', 'cleaning', 'preprocessing']):
            return 'data_curation'
        else:
            return 'general'
    
    def _analyze_trading_strategy(self, results: Dict[str, Any], patterns: Dict[str, Any]) -> tuple:
        """Analyze trading strategy experiment results"""
        key_insights = []
        recommendations = []
        validation_passed = True
        
        sharpe = results.get('sharpe_ratio', 0)
        max_drawdown = results.get('max_drawdown', 1.0)
        win_rate = results.get('win_rate', 0)
        
        # Key insight generation
        if sharpe > 1.5:
            key_insights.append(f"Exceptional Sharpe ratio: {sharpe:.2f} indicates strong alpha generation")
        if max_drawdown < 0.1:
            key_insights.append(f"Excellent risk control: max drawdown {max_drawdown:.2f}% below threshold")
        else:
            key_insights.append(f"Risk management needs improvement: max drawdown {max_drawdown:.2f}%")
        
        if win_rate > 0.6:
            key_insights.append(f"High win rate: {win_rate:.2f}% suggests effective strategy")
            recommendations.append("Increase position size during high-confidence periods")
        else:
            recommendations.append("Review strategy logic and risk management parameters")
        
        validation_passed = (
            sharpe > patterns['success_thresholds']['sharpe_ratio'] and
            max_drawdown < 0.15 and
            win_rate > patterns['success_thresholds']['win_rate']
        )
        
        return key_insights, recommendations, validation_passed
    
    def _analyze_ml_architecture(self, results: Dict[str, Any], patterns: Dict[str, Any]) -> tuple:
        """Analyze ML architecture experiment results"""
        key_insights = []
        recommendations = []
        validation_passed = True
        
        accuracy = results.get('accuracy', 0)
        training_time = results.get('training_time', 0)
        inference_time = results.get('inference_time', 0)
        
        # Key insight generation
        if accuracy > 0.85 and inference_time < 50:
            key_insights.append(f"High efficiency: accuracy {accuracy:.3f} with fast inference ({inference_time}ms)")
        elif training_time > 300:
            key_insights.append(f"Potential overfitting: long training time ({training_time}s)")
        
        if accuracy > 0.8:
            recommendations.append("Architecture ready for deployment consideration")
        else:
            recommendations.append("Focus on fundamental architecture improvements")
        
        validation_passed = accuracy > patterns['success_thresholds']['accuracy']
        
        return key_insights, recommendations, validation_passed
    
    def _analyze_data_curation(self, results: Dict[str, Any], patterns: Dict[str, Any]) -> tuple:
        """Analyze data curation experiment results"""
        key_insights = []
        recommendations = []
        validation_passed = True
        
        quality = results.get('data_quality', 0)
        completeness = results.get('completeness', 0)
        improvement = results.get('improvement_score', 0)
        
        # Key insight generation
        if quality > 0.85 and completeness > 0.9:
            key_insights.append(f"High-quality curation: quality {quality:.2f}, completeness {completeness:.2f}")
        elif improvement > 0.1:
            key_insights.append(f"Consistent improvement: {improvement:.2f} increase over baseline")
        
        if completeness < 0.7:
            recommendations.append("Focus on domain-specific data sources")
        else:
            recommendations.append("Curation strategy appears effective")
        
        validation_passed = (
            quality > patterns['success_thresholds']['data_quality'] and
            completeness > patterns['success_thresholds']['completeness']
        )
        
        return key_insights, recommendations, validation_passed
    
    def _analyze_trends(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends across multiple metrics"""
        trends = {}
        
        # Simple trend analysis based on score progression
        if 'score_history' in results:
            scores = results['score_history']
            if len(scores) > 1:
                recent_trend = 'improving' if scores[-1] > scores[-2] else 'declining'
                trends['score_trend'] = recent_trend
                trends['score_volatility'] = np.std(scores[-5:]) if len(scores) >= 5 else 0
        
        return trends
    
    def get_analysis_history(self, domain: Optional[str] = None) -> List[AnalysisReport]:
        """Get analysis history for specific domain"""
        if domain:
            return [report for report in self.analysis_history if report.created_at and 
                   any(keyword in report.to_dict()['key_insights'][0] for keyword in 
                       self.analysis_patterns.get(domain, {}).get('insight_patterns', []))]
        return self.analysis_history
