"""
Self-Analysis Module
=====================

Automated system for analyzing and improving trading performance:
- Trade Attribution Analysis
- Model Performance Tracking
- Anomaly Detection
- Continuous Improvement Recommendations
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class IssueType(Enum):
    """Types of identified issues"""
    MODEL_DEGRADATION = "model_degradation"
    EXECUTION_QUALITY = "execution_quality"
    RISK_MANAGEMENT = "risk_management"
    DATA_QUALITY = "data_quality"
    STRATEGY_DRIFT = "strategy_drift"
    MARKET_REGIME_CHANGE = "market_regime_change"


class IssueSeverity(Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IdentifiedIssue:
    """An identified issue from self-analysis"""
    issue_id: str
    timestamp: datetime
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    evidence: Dict[str, Any]
    recommendation: str
    auto_fixable: bool = False
    fixed: bool = False


@dataclass
class PerformanceReport:
    """Periodic performance report"""
    period_start: datetime
    period_end: datetime
    
    # Performance metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    
    # Comparison to benchmark
    vs_benchmark: float
    vs_previous_period: float
    
    # Attribution
    alpha_contribution: float
    beta_contribution: float
    factor_contributions: Dict[str, float]
    
    # Issues identified
    issues: List[IdentifiedIssue]
    
    # Recommendations
    recommendations: List[str]


class TradeAttributionAnalyzer:
    """
    Analyzes trade performance attribution
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Trade history
        self.trades: deque = deque(maxlen=10000)
        
        # Attribution categories
        self.categories = [
            'signal_source', 'strategy', 'symbol', 'time_of_day',
            'day_of_week', 'market_regime', 'position_size'
        ]
    
    def add_trade(self, trade: Dict[str, Any]):
        """Add trade for analysis"""
        self.trades.append(trade)
    
    def analyze_attribution(self) -> Dict[str, Dict[str, Any]]:
        """Analyze P&L attribution by various factors"""
        if not self.trades:
            return {}
        
        attribution = {}
        
        for category in self.categories:
            attribution[category] = self._analyze_category(category)
        
        return attribution
    
    def _analyze_category(self, category: str) -> Dict[str, Any]:
        """Analyze attribution for a specific category"""
        grouped = {}
        
        for trade in self.trades:
            key = trade.get(category, 'unknown')
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(trade.get('pnl', 0))
        
        results = {}
        for key, pnls in grouped.items():
            if pnls:
                results[key] = {
                    'total_pnl': sum(pnls),
                    'avg_pnl': np.mean(pnls),
                    'trade_count': len(pnls),
                    'win_rate': sum(1 for p in pnls if p > 0) / len(pnls),
                    'sharpe': np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252),
                }
        
        return results
    
    def identify_underperformers(self, threshold: float = 0) -> List[Dict[str, Any]]:
        """Identify underperforming categories"""
        attribution = self.analyze_attribution()
        underperformers = []
        
        for category, results in attribution.items():
            for key, metrics in results.items():
                if metrics['total_pnl'] < threshold and metrics['trade_count'] >= 10:
                    underperformers.append({
                        'category': category,
                        'key': key,
                        'metrics': metrics,
                    })
        
        return sorted(underperformers, key=lambda x: x['metrics']['total_pnl'])
    
    def get_best_performers(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get best performing categories"""
        attribution = self.analyze_attribution()
        performers = []
        
        for category, results in attribution.items():
            for key, metrics in results.items():
                if metrics['trade_count'] >= 10:
                    performers.append({
                        'category': category,
                        'key': key,
                        'metrics': metrics,
                    })
        
        return sorted(performers, key=lambda x: x['metrics']['sharpe'], reverse=True)[:top_n]


class ModelPerformanceTracker:
    """
    Tracks and analyzes model performance over time
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Model predictions and outcomes
        self.predictions: Dict[str, deque] = {}
        
        # Performance metrics history
        self.metrics_history: Dict[str, deque] = {}
        
        # Degradation thresholds
        self.degradation_threshold = self.config.get('degradation_threshold', 0.1)
        self.min_samples = self.config.get('min_samples', 50)
    
    def record_prediction(self, model_name: str, prediction: Dict[str, Any],
                         actual: Dict[str, Any]):
        """Record model prediction and actual outcome"""
        if model_name not in self.predictions:
            self.predictions[model_name] = deque(maxlen=1000)
        
        self.predictions[model_name].append({
            'timestamp': datetime.now(),
            'prediction': prediction,
            'actual': actual,
            'correct': self._is_correct(prediction, actual),
        })
    
    def _is_correct(self, prediction: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """Check if prediction was correct"""
        pred_direction = prediction.get('direction', 'neutral')
        actual_return = actual.get('return', 0)
        
        if pred_direction == 'long' and actual_return > 0:
            return True
        elif pred_direction == 'short' and actual_return < 0:
            return True
        elif pred_direction == 'neutral' and abs(actual_return) < 0.001:
            return True
        return False
    
    def calculate_metrics(self, model_name: str, lookback: int = 100) -> Dict[str, float]:
        """Calculate performance metrics for a model"""
        if model_name not in self.predictions:
            return {}
        
        recent = list(self.predictions[model_name])[-lookback:]
        
        if len(recent) < self.min_samples:
            return {'accuracy': 0.5, 'sample_size': len(recent)}
        
        correct = sum(1 for p in recent if p['correct'])
        accuracy = correct / len(recent)
        
        # Calculate returns
        returns = []
        for p in recent:
            if p['prediction'].get('direction') == 'long':
                returns.append(p['actual'].get('return', 0))
            elif p['prediction'].get('direction') == 'short':
                returns.append(-p['actual'].get('return', 0))
        
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252) if returns else 0
        
        return {
            'accuracy': accuracy,
            'sharpe': sharpe,
            'sample_size': len(recent),
            'win_rate': accuracy,
        }
    
    def detect_degradation(self, model_name: str) -> Optional[IdentifiedIssue]:
        """Detect model performance degradation"""
        if model_name not in self.predictions:
            return None
        
        predictions = list(self.predictions[model_name])
        
        if len(predictions) < self.min_samples * 2:
            return None
        
        # Compare recent vs older performance
        mid_point = len(predictions) // 2
        older = predictions[:mid_point]
        recent = predictions[mid_point:]
        
        older_accuracy = sum(1 for p in older if p['correct']) / len(older)
        recent_accuracy = sum(1 for p in recent if p['correct']) / len(recent)
        
        degradation = older_accuracy - recent_accuracy
        
        if degradation > self.degradation_threshold:
            return IdentifiedIssue(
                issue_id=f"DEG_{model_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(),
                issue_type=IssueType.MODEL_DEGRADATION,
                severity=IssueSeverity.HIGH if degradation > 0.2 else IssueSeverity.MEDIUM,
                description=f"Model {model_name} accuracy dropped from {older_accuracy:.2%} to {recent_accuracy:.2%}",
                evidence={
                    'older_accuracy': older_accuracy,
                    'recent_accuracy': recent_accuracy,
                    'degradation': degradation,
                    'sample_size': len(predictions),
                },
                recommendation=f"Consider retraining {model_name} or adjusting its weight in the ensemble",
                auto_fixable=False,
            )
        
        return None
    
    def get_all_model_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get metrics for all tracked models"""
        return {
            model_name: self.calculate_metrics(model_name)
            for model_name in self.predictions.keys()
        }


class AnomalyDetector:
    """
    Detects anomalies in trading behavior and market conditions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Feature history
        self.feature_history: deque = deque(maxlen=1000)
        
        # Anomaly detector
        if SKLEARN_AVAILABLE:
            self.detector = IsolationForest(
                contamination=self.config.get('contamination', 0.1),
                random_state=42
            )
            self.scaler = StandardScaler()
            self.is_fitted = False
        else:
            self.detector = None
            self.is_fitted = False
        
        # Detected anomalies
        self.anomalies: deque = deque(maxlen=100)
    
    def add_observation(self, features: Dict[str, float]):
        """Add observation for anomaly detection"""
        self.feature_history.append({
            'timestamp': datetime.now(),
            'features': features,
        })
    
    def fit(self):
        """Fit anomaly detector on historical data"""
        if not SKLEARN_AVAILABLE or self.detector is None:
            return
        
        if len(self.feature_history) < 100:
            return
        
        # Extract features
        feature_names = list(self.feature_history[0]['features'].keys())
        X = np.array([
            [obs['features'].get(f, 0) for f in feature_names]
            for obs in self.feature_history
        ])
        
        # Scale and fit
        X_scaled = self.scaler.fit_transform(X)
        self.detector.fit(X_scaled)
        self.is_fitted = True
    
    def detect(self, features: Dict[str, float]) -> Optional[IdentifiedIssue]:
        """Detect if current observation is anomalous"""
        if not SKLEARN_AVAILABLE or not self.is_fitted:
            return self._rule_based_detection(features)
        
        # Prepare features
        feature_names = list(self.feature_history[0]['features'].keys())
        X = np.array([[features.get(f, 0) for f in feature_names]])
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.detector.predict(X_scaled)[0]
        
        if prediction == -1:  # Anomaly
            return IdentifiedIssue(
                issue_id=f"ANOM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(),
                issue_type=IssueType.DATA_QUALITY,
                severity=IssueSeverity.MEDIUM,
                description="Anomalous market conditions detected",
                evidence={'features': features},
                recommendation="Review current positions and consider reducing exposure",
                auto_fixable=False,
            )
        
        return None
    
    def _rule_based_detection(self, features: Dict[str, float]) -> Optional[IdentifiedIssue]:
        """Fallback rule-based anomaly detection"""
        anomalies = []
        
        # Check for extreme values
        if features.get('volatility', 0) > 0.05:
            anomalies.append('High volatility')
        
        if abs(features.get('return', 0)) > 0.05:
            anomalies.append('Large price move')
        
        if features.get('spread', 0) > 0.01:
            anomalies.append('Wide spread')
        
        if features.get('volume_ratio', 1) > 3:
            anomalies.append('Unusual volume')
        
        if anomalies:
            return IdentifiedIssue(
                issue_id=f"ANOM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(),
                issue_type=IssueType.MARKET_REGIME_CHANGE,
                severity=IssueSeverity.MEDIUM,
                description=f"Anomalies detected: {', '.join(anomalies)}",
                evidence={'features': features, 'anomalies': anomalies},
                recommendation="Review current positions and consider reducing exposure",
                auto_fixable=False,
            )
        
        return None


class ContinuousImprover:
    """
    Generates continuous improvement recommendations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Components
        self.attribution_analyzer = TradeAttributionAnalyzer()
        self.model_tracker = ModelPerformanceTracker()
        self.anomaly_detector = AnomalyDetector()
        
        # Issue history
        self.issues: deque = deque(maxlen=1000)
        
        # Recommendations
        self.recommendations: List[str] = []
    
    def analyze(self, trades: List[Dict[str, Any]], 
               model_predictions: Dict[str, List[Dict[str, Any]]],
               market_features: Dict[str, float]) -> PerformanceReport:
        """
        Run comprehensive analysis
        
        Args:
            trades: Recent trades
            model_predictions: Model predictions and outcomes
            market_features: Current market features
            
        Returns:
            PerformanceReport
        """
        issues = []
        recommendations = []
        
        # Add trades for attribution
        for trade in trades:
            self.attribution_analyzer.add_trade(trade)
        
        # Check for underperformers
        underperformers = self.attribution_analyzer.identify_underperformers()
        for up in underperformers[:3]:
            issues.append(IdentifiedIssue(
                issue_id=f"UNDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(),
                issue_type=IssueType.STRATEGY_DRIFT,
                severity=IssueSeverity.MEDIUM,
                description=f"Underperforming: {up['category']}={up['key']}",
                evidence=up['metrics'],
                recommendation=f"Consider reducing allocation to {up['category']}={up['key']}",
                auto_fixable=False,
            ))
            recommendations.append(f"Review {up['category']}={up['key']} strategy")
        
        # Check model performance
        for model_name, predictions in model_predictions.items():
            for pred in predictions:
                self.model_tracker.record_prediction(
                    model_name, pred.get('prediction', {}), pred.get('actual', {})
                )
            
            degradation = self.model_tracker.detect_degradation(model_name)
            if degradation:
                issues.append(degradation)
                recommendations.append(degradation.recommendation)
        
        # Check for anomalies
        self.anomaly_detector.add_observation(market_features)
        anomaly = self.anomaly_detector.detect(market_features)
        if anomaly:
            issues.append(anomaly)
            recommendations.append(anomaly.recommendation)
        
        # Store issues
        for issue in issues:
            self.issues.append(issue)
        
        # Calculate performance metrics
        if trades:
            pnls = [t.get('pnl', 0) for t in trades]
            total_return = sum(pnls) / self.config.get('capital', 100000)
            sharpe = np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252) if pnls else 0
            
            wins = [p for p in pnls if p > 0]
            win_rate = len(wins) / len(pnls) if pnls else 0
            
            # Max drawdown
            cumulative = np.cumsum(pnls)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = running_max - cumulative
            max_drawdown = np.max(drawdown) / self.config.get('capital', 100000) if len(drawdown) > 0 else 0
        else:
            total_return = sharpe = win_rate = max_drawdown = 0
        
        return PerformanceReport(
            period_start=trades[0].get('timestamp', datetime.now()) if trades else datetime.now(),
            period_end=trades[-1].get('timestamp', datetime.now()) if trades else datetime.now(),
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            vs_benchmark=0,  # Would need benchmark data
            vs_previous_period=0,  # Would need previous period data
            alpha_contribution=total_return * 0.7,  # Simplified
            beta_contribution=total_return * 0.3,  # Simplified
            factor_contributions={},
            issues=issues,
            recommendations=recommendations,
        )
    
    def get_improvement_plan(self) -> List[Dict[str, Any]]:
        """Generate prioritized improvement plan"""
        plan = []
        
        # Analyze recent issues
        recent_issues = list(self.issues)[-50:]
        
        # Group by type
        issue_counts = {}
        for issue in recent_issues:
            issue_type = issue.issue_type.value
            if issue_type not in issue_counts:
                issue_counts[issue_type] = 0
            issue_counts[issue_type] += 1
        
        # Generate plan items
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 3:
                plan.append({
                    'priority': 'high' if count >= 5 else 'medium',
                    'area': issue_type,
                    'issue_count': count,
                    'action': self._get_action_for_issue_type(issue_type),
                })
        
        # Add best performers to leverage
        best = self.attribution_analyzer.get_best_performers(3)
        for performer in best:
            plan.append({
                'priority': 'medium',
                'area': 'leverage_strength',
                'detail': f"{performer['category']}={performer['key']}",
                'action': f"Consider increasing allocation to {performer['category']}={performer['key']}",
            })
        
        return plan
    
    def _get_action_for_issue_type(self, issue_type: str) -> str:
        """Get recommended action for issue type"""
        actions = {
            'model_degradation': 'Schedule model retraining and review feature engineering',
            'execution_quality': 'Review execution algorithms and venue selection',
            'risk_management': 'Tighten risk limits and review position sizing',
            'data_quality': 'Audit data pipelines and add validation checks',
            'strategy_drift': 'Review strategy parameters and market conditions',
            'market_regime_change': 'Adjust strategy weights for new regime',
        }
        return actions.get(issue_type, 'Investigate and address root cause')


class SelfAnalysisEngine:
    """
    Main self-analysis engine
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Components
        self.improver = ContinuousImprover(config)
        
        # Analysis history
        self.reports: deque = deque(maxlen=100)
        
        # Scheduled analysis
        self.last_analysis = datetime.now()
        self.analysis_interval = timedelta(hours=self.config.get('analysis_interval_hours', 24))
    
    def should_analyze(self) -> bool:
        """Check if analysis should run"""
        return datetime.now() - self.last_analysis > self.analysis_interval
    
    def run_analysis(self, trades: List[Dict[str, Any]],
                    model_predictions: Dict[str, List[Dict[str, Any]]],
                    market_features: Dict[str, float]) -> PerformanceReport:
        """Run self-analysis"""
        report = self.improver.analyze(trades, model_predictions, market_features)
        
        self.reports.append(report)
        self.last_analysis = datetime.now()
        
        # Log summary
        logger.info(f"Self-analysis complete: Return={report.total_return:.2%}, "
                   f"Sharpe={report.sharpe_ratio:.2f}, Issues={len(report.issues)}")
        
        return report
    
    def get_improvement_plan(self) -> List[Dict[str, Any]]:
        """Get improvement plan"""
        return self.improver.get_improvement_plan()
    
    def get_recent_issues(self, severity: IssueSeverity = None) -> List[IdentifiedIssue]:
        """Get recent issues, optionally filtered by severity"""
        issues = list(self.improver.issues)
        
        if severity:
            issues = [i for i in issues if i.severity == severity]
        
        return sorted(issues, key=lambda i: i.timestamp, reverse=True)
