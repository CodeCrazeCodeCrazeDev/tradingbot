"""
Predictive Systems
==================

Advanced predictive capabilities including:
- Predictive Maintenance for Trading Systems
- Risk Prediction and Early Warning
- Market Regime Prediction
- Causal Discovery for Market Dynamics
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# PREDICTIVE MAINTENANCE FOR TRADING SYSTEMS
# =============================================================================

class ComponentStatus(Enum):
    """Status of system components"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class ComponentHealth:
    """Health metrics for a component"""
    component_id: str
    name: str
    status: ComponentStatus
    health_score: float  # 0-1
    metrics: Dict[str, float]
    last_updated: datetime = field(default_factory=datetime.utcnow)
    predicted_failure_time: Optional[datetime] = None
    failure_probability: float = 0.0


@dataclass
class MaintenanceAction:
    """A recommended maintenance action"""
    action_id: str
    component_id: str
    action_type: str
    priority: int
    description: str
    estimated_downtime: timedelta
    recommended_time: datetime


class PredictiveMaintenanceSystem:
    """
    Predictive Maintenance for Trading Systems
    
    Monitors system components and predicts failures
    before they occur.
    """
    
    def __init__(
        self,
        prediction_horizon_hours: int = 24,
        health_history_size: int = 1000
    ):
        self.prediction_horizon = timedelta(hours=prediction_horizon_hours)
        self.health_history_size = health_history_size
        
        self.components: Dict[str, ComponentHealth] = {}
        self.health_history: Dict[str, deque] = {}
        self.maintenance_schedule: List[MaintenanceAction] = []
        
        # Failure prediction models (simplified)
        self.failure_thresholds = {
            'latency': 100,  # ms
            'error_rate': 0.05,
            'memory_usage': 0.9,
            'cpu_usage': 0.95,
            'queue_depth': 1000
        }
        
        logger.info("PredictiveMaintenanceSystem initialized")
    
    def register_component(
        self,
        component_id: str,
        name: str,
        initial_metrics: Dict[str, float] = None
    ) -> ComponentHealth:
        """Register a system component for monitoring"""
        
        health = ComponentHealth(
            component_id=component_id,
            name=name,
            status=ComponentStatus.HEALTHY,
            health_score=1.0,
            metrics=initial_metrics or {}
        )
        
        self.components[component_id] = health
        self.health_history[component_id] = deque(maxlen=self.health_history_size)
        
        logger.info(f"Registered component: {name}")
        return health
    
    def update_metrics(
        self,
        component_id: str,
        metrics: Dict[str, float]
    ) -> ComponentHealth:
        """Update component metrics"""
        
        if component_id not in self.components:
            raise ValueError(f"Unknown component: {component_id}")
        
        health = self.components[component_id]
        health.metrics.update(metrics)
        health.last_updated = datetime.utcnow()
        
        # Record history
        self.health_history[component_id].append({
            'timestamp': health.last_updated,
            'metrics': metrics.copy()
        })
        
        # Calculate health score
        health.health_score = self._calculate_health_score(metrics)
        health.status = self._determine_status(health.health_score)
        
        # Predict failure
        failure_prob, failure_time = self._predict_failure(component_id)
        health.failure_probability = failure_prob
        health.predicted_failure_time = failure_time
        
        return health
    
    def _calculate_health_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall health score from metrics"""
        
        scores = []
        
        for metric_name, value in metrics.items():
            if metric_name in self.failure_thresholds:
                threshold = self.failure_thresholds[metric_name]
                # Score decreases as value approaches threshold
                score = max(0, 1 - value / threshold)
                scores.append(score)
        
        if not scores:
            return 1.0
        
        return np.mean(scores)
    
    def _determine_status(self, health_score: float) -> ComponentStatus:
        """Determine component status from health score"""
        
        if health_score >= 0.9:
            return ComponentStatus.HEALTHY
        elif health_score >= 0.7:
            return ComponentStatus.DEGRADED
        elif health_score >= 0.5:
            return ComponentStatus.WARNING
        elif health_score >= 0.2:
            return ComponentStatus.CRITICAL
        else:
            return ComponentStatus.FAILED
    
    def _predict_failure(
        self,
        component_id: str
    ) -> Tuple[float, Optional[datetime]]:
        """Predict component failure"""
        
        history = list(self.health_history[component_id])
        
        if len(history) < 10:
            return 0.0, None
        
        # Extract health scores over time
        scores = []
        for entry in history[-50:]:
            metrics = entry['metrics']
            score = self._calculate_health_score(metrics)
            scores.append(score)
        
        # Trend analysis
        if len(scores) >= 2:
            trend = (scores[-1] - scores[0]) / len(scores)
            
            if trend < -0.01:  # Declining health
                # Estimate time to failure
                current_score = scores[-1]
                
                if trend != 0:
                    steps_to_failure = current_score / abs(trend)
                    # Assume 1 minute per step
                    failure_time = datetime.utcnow() + timedelta(minutes=steps_to_failure)
                    
                    # Failure probability based on trend severity
                    failure_prob = min(1.0, abs(trend) * 100)
                    
                    return failure_prob, failure_time
        
        return 0.0, None
    
    def generate_maintenance_recommendations(self) -> List[MaintenanceAction]:
        """Generate maintenance recommendations"""
        
        recommendations = []
        
        for component_id, health in self.components.items():
            if health.failure_probability > 0.3:
                action = MaintenanceAction(
                    action_id=f"maint_{component_id}_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                    component_id=component_id,
                    action_type="preventive_restart",
                    priority=1 if health.failure_probability > 0.7 else 2,
                    description=f"Preventive maintenance for {health.name}",
                    estimated_downtime=timedelta(minutes=5),
                    recommended_time=datetime.utcnow() + timedelta(hours=1)
                )
                recommendations.append(action)
            
            elif health.status == ComponentStatus.DEGRADED:
                action = MaintenanceAction(
                    action_id=f"check_{component_id}_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                    component_id=component_id,
                    action_type="health_check",
                    priority=3,
                    description=f"Health check for {health.name}",
                    estimated_downtime=timedelta(minutes=1),
                    recommended_time=datetime.utcnow() + timedelta(hours=4)
                )
                recommendations.append(action)
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority)
        self.maintenance_schedule = recommendations
        
        return recommendations
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_health': np.mean([c.health_score for c in self.components.values()]) if self.components else 1.0,
            'components': {
                cid: {
                    'name': c.name,
                    'status': c.status.value,
                    'health_score': c.health_score,
                    'failure_probability': c.failure_probability,
                    'predicted_failure': c.predicted_failure_time.isoformat() if c.predicted_failure_time else None
                }
                for cid, c in self.components.items()
            },
            'pending_maintenance': len(self.maintenance_schedule),
            'critical_components': [
                c.name for c in self.components.values()
                if c.status in [ComponentStatus.CRITICAL, ComponentStatus.FAILED]
            ]
        }


# =============================================================================
# RISK PREDICTION AND EARLY WARNING
# =============================================================================

class RiskLevel(Enum):
    """Risk levels"""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class RiskAlert:
    """A risk alert"""
    alert_id: str
    risk_type: str
    level: RiskLevel
    probability: float
    impact: float
    description: str
    recommended_actions: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires: Optional[datetime] = None


class RiskPredictionSystem:
    """
    Risk Prediction and Early Warning
    
    Predicts various types of risks and provides
    early warnings.
    """
    
    def __init__(self):
        self.risk_models: Dict[str, Callable] = {}
        self.active_alerts: List[RiskAlert] = []
        self.alert_history: List[RiskAlert] = []
        
        # Register default risk models
        self._register_default_models()
        
        logger.info("RiskPredictionSystem initialized")
    
    def _register_default_models(self):
        """Register default risk prediction models"""
        
        self.risk_models['volatility_spike'] = self._predict_volatility_spike
        self.risk_models['drawdown'] = self._predict_drawdown
        self.risk_models['liquidity_crisis'] = self._predict_liquidity_crisis
        self.risk_models['correlation_breakdown'] = self._predict_correlation_breakdown
        self.risk_models['tail_risk'] = self._predict_tail_risk
    
    def _predict_volatility_spike(
        self,
        returns: np.ndarray,
        current_vol: float
    ) -> Tuple[float, RiskLevel]:
        """Predict volatility spike risk"""
        
        if len(returns) < 20:
            return 0.0, RiskLevel.LOW
        
        historical_vol = np.std(returns[-60:]) if len(returns) >= 60 else np.std(returns)
        vol_ratio = current_vol / (historical_vol + 1e-10)
        
        if vol_ratio > 3:
            return 0.9, RiskLevel.EXTREME
        elif vol_ratio > 2:
            return 0.7, RiskLevel.HIGH
        elif vol_ratio > 1.5:
            return 0.5, RiskLevel.ELEVATED
        elif vol_ratio > 1.2:
            return 0.3, RiskLevel.MODERATE
        else:
            return 0.1, RiskLevel.LOW
    
    def _predict_drawdown(
        self,
        equity_curve: np.ndarray,
        current_drawdown: float
    ) -> Tuple[float, RiskLevel]:
        """Predict drawdown risk"""
        
        if current_drawdown > 0.2:
            return 0.9, RiskLevel.EXTREME
        elif current_drawdown > 0.15:
            return 0.7, RiskLevel.HIGH
        elif current_drawdown > 0.1:
            return 0.5, RiskLevel.ELEVATED
        elif current_drawdown > 0.05:
            return 0.3, RiskLevel.MODERATE
        else:
            return 0.1, RiskLevel.LOW
    
    def _predict_liquidity_crisis(
        self,
        volume: np.ndarray,
        spread: np.ndarray
    ) -> Tuple[float, RiskLevel]:
        """Predict liquidity crisis risk"""
        
        if len(volume) < 10 or len(spread) < 10:
            return 0.0, RiskLevel.LOW
        
        # Volume decline
        recent_vol = np.mean(volume[-5:])
        historical_vol = np.mean(volume[-30:]) if len(volume) >= 30 else np.mean(volume)
        vol_ratio = recent_vol / (historical_vol + 1e-10)
        
        # Spread widening
        recent_spread = np.mean(spread[-5:])
        historical_spread = np.mean(spread[-30:]) if len(spread) >= 30 else np.mean(spread)
        spread_ratio = recent_spread / (historical_spread + 1e-10)
        
        risk_score = (1 - vol_ratio) * 0.5 + (spread_ratio - 1) * 0.5
        risk_score = np.clip(risk_score, 0, 1)
        
        if risk_score > 0.8:
            return risk_score, RiskLevel.EXTREME
        elif risk_score > 0.6:
            return risk_score, RiskLevel.HIGH
        elif risk_score > 0.4:
            return risk_score, RiskLevel.ELEVATED
        elif risk_score > 0.2:
            return risk_score, RiskLevel.MODERATE
        else:
            return risk_score, RiskLevel.LOW
    
    def _predict_correlation_breakdown(
        self,
        asset_returns: Dict[str, np.ndarray],
        lookback: int = 60
    ) -> Tuple[float, RiskLevel]:
        """Predict correlation breakdown risk"""
        
        if len(asset_returns) < 2:
            return 0.0, RiskLevel.LOW
        
        assets = list(asset_returns.keys())
        
        # Calculate recent vs historical correlations
        correlation_changes = []
        
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                returns1 = asset_returns[asset1]
                returns2 = asset_returns[asset2]
                
                if len(returns1) < lookback or len(returns2) < lookback:
                    continue
                
                # Recent correlation
                recent_corr = np.corrcoef(returns1[-20:], returns2[-20:])[0, 1]
                
                # Historical correlation
                hist_corr = np.corrcoef(returns1[-lookback:-20], returns2[-lookback:-20])[0, 1]
                
                if np.isfinite(recent_corr) and np.isfinite(hist_corr):
                    change = abs(recent_corr - hist_corr)
                    correlation_changes.append(change)
        
        if not correlation_changes:
            return 0.0, RiskLevel.LOW
        
        avg_change = np.mean(correlation_changes)
        
        if avg_change > 0.5:
            return 0.9, RiskLevel.EXTREME
        elif avg_change > 0.3:
            return 0.7, RiskLevel.HIGH
        elif avg_change > 0.2:
            return 0.5, RiskLevel.ELEVATED
        elif avg_change > 0.1:
            return 0.3, RiskLevel.MODERATE
        else:
            return 0.1, RiskLevel.LOW
    
    def _predict_tail_risk(
        self,
        returns: np.ndarray,
        confidence: float = 0.99
    ) -> Tuple[float, RiskLevel]:
        """Predict tail risk (extreme events)"""
        
        if len(returns) < 100:
            return 0.0, RiskLevel.LOW
        
        # Calculate VaR and CVaR
        var = np.percentile(returns, (1 - confidence) * 100)
        cvar = np.mean(returns[returns <= var])
        
        # Recent extreme moves
        recent_returns = returns[-20:]
        extreme_count = np.sum(recent_returns <= var)
        
        expected_extremes = len(recent_returns) * (1 - confidence)
        
        if extreme_count > expected_extremes * 3:
            return 0.9, RiskLevel.EXTREME
        elif extreme_count > expected_extremes * 2:
            return 0.7, RiskLevel.HIGH
        elif extreme_count > expected_extremes * 1.5:
            return 0.5, RiskLevel.ELEVATED
        elif extreme_count > expected_extremes:
            return 0.3, RiskLevel.MODERATE
        else:
            return 0.1, RiskLevel.LOW
    
    def assess_risks(
        self,
        market_data: Dict[str, Any]
    ) -> List[RiskAlert]:
        """Assess all risks and generate alerts"""
        
        alerts = []
        
        # Volatility risk
        if 'returns' in market_data:
            returns = market_data['returns']
            current_vol = np.std(returns[-20:]) if len(returns) >= 20 else np.std(returns)
            prob, level = self._predict_volatility_spike(returns, current_vol)
            
            if level.value in ['elevated', 'high', 'extreme']:
                alerts.append(RiskAlert(
                    alert_id=f"vol_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    risk_type="volatility_spike",
                    level=level,
                    probability=prob,
                    impact=0.7,
                    description="Elevated volatility detected",
                    recommended_actions=["Reduce position sizes", "Tighten stops"]
                ))
        
        # Drawdown risk
        if 'equity_curve' in market_data:
            equity = market_data['equity_curve']
            peak = np.max(equity)
            current_dd = (peak - equity[-1]) / peak if peak > 0 else 0
            prob, level = self._predict_drawdown(equity, current_dd)
            
            if level.value in ['elevated', 'high', 'extreme']:
                alerts.append(RiskAlert(
                    alert_id=f"dd_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    risk_type="drawdown",
                    level=level,
                    probability=prob,
                    impact=0.9,
                    description=f"Drawdown at {current_dd*100:.1f}%",
                    recommended_actions=["Review positions", "Consider hedging"]
                ))
        
        # Update active alerts
        self.active_alerts = alerts
        self.alert_history.extend(alerts)
        
        return alerts
    
    def get_risk_dashboard(self) -> Dict[str, Any]:
        """Get risk dashboard data"""
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'active_alerts': len(self.active_alerts),
            'highest_risk': max(
                (a.level.value for a in self.active_alerts),
                default='low'
            ),
            'alerts': [
                {
                    'type': a.risk_type,
                    'level': a.level.value,
                    'probability': a.probability,
                    'description': a.description
                }
                for a in self.active_alerts
            ],
            'risk_models': list(self.risk_models.keys())
        }


# =============================================================================
# MARKET REGIME PREDICTION
# =============================================================================

class MarketRegime(Enum):
    """Market regime types"""
    BULL_QUIET = "bull_quiet"
    BULL_VOLATILE = "bull_volatile"
    BEAR_QUIET = "bear_quiet"
    BEAR_VOLATILE = "bear_volatile"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"
    RECOVERY = "recovery"


@dataclass
class RegimePrediction:
    """A regime prediction"""
    current_regime: MarketRegime
    regime_probabilities: Dict[MarketRegime, float]
    transition_probabilities: Dict[MarketRegime, float]
    confidence: float
    duration_estimate: int  # bars
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MarketRegimePredictor:
    """
    Market Regime Prediction
    
    Predicts current and future market regimes
    for adaptive strategy selection.
    """
    
    def __init__(self, lookback: int = 60):
        self.lookback = lookback
        
        # Hidden Markov Model parameters (simplified)
        self.num_regimes = len(MarketRegime)
        self.transition_matrix = np.ones((self.num_regimes, self.num_regimes)) / self.num_regimes
        
        # Regime characteristics
        self.regime_params = {
            MarketRegime.BULL_QUIET: {'mean': 0.001, 'std': 0.01},
            MarketRegime.BULL_VOLATILE: {'mean': 0.002, 'std': 0.03},
            MarketRegime.BEAR_QUIET: {'mean': -0.001, 'std': 0.01},
            MarketRegime.BEAR_VOLATILE: {'mean': -0.002, 'std': 0.03},
            MarketRegime.SIDEWAYS: {'mean': 0.0, 'std': 0.008},
            MarketRegime.CRISIS: {'mean': -0.005, 'std': 0.05},
            MarketRegime.RECOVERY: {'mean': 0.003, 'std': 0.025}
        }
        
        self.regime_history: List[MarketRegime] = []
        
        logger.info("MarketRegimePredictor initialized")
    
    def detect_regime(self, returns: np.ndarray) -> MarketRegime:
        """Detect current market regime"""
        
        if len(returns) < 20:
            return MarketRegime.SIDEWAYS
        
        recent_returns = returns[-self.lookback:] if len(returns) >= self.lookback else returns
        
        mean_return = np.mean(recent_returns)
        volatility = np.std(recent_returns)
        
        # Trend detection
        cumulative = np.cumsum(recent_returns)
        trend = (cumulative[-1] - cumulative[0]) / len(cumulative)
        
        # Classify regime
        is_bullish = mean_return > 0.0005
        is_bearish = mean_return < -0.0005
        is_volatile = volatility > 0.02
        is_crisis = volatility > 0.04 and mean_return < -0.002
        
        if is_crisis:
            return MarketRegime.CRISIS
        elif is_bullish and is_volatile:
            return MarketRegime.BULL_VOLATILE
        elif is_bullish:
            return MarketRegime.BULL_QUIET
        elif is_bearish and is_volatile:
            return MarketRegime.BEAR_VOLATILE
        elif is_bearish:
            return MarketRegime.BEAR_QUIET
        elif mean_return > 0.001 and volatility > 0.015:
            return MarketRegime.RECOVERY
        else:
            return MarketRegime.SIDEWAYS
    
    def predict_regime(
        self,
        returns: np.ndarray,
        horizon: int = 10
    ) -> RegimePrediction:
        """Predict current and future regimes"""
        
        current_regime = self.detect_regime(returns)
        self.regime_history.append(current_regime)
        
        # Calculate regime probabilities using emission likelihoods
        regime_probs = {}
        recent_returns = returns[-20:] if len(returns) >= 20 else returns
        
        for regime in MarketRegime:
            params = self.regime_params[regime]
            # Gaussian likelihood
            likelihood = np.prod(
                np.exp(-0.5 * ((recent_returns - params['mean']) / params['std'])**2) /
                (params['std'] * np.sqrt(2 * np.pi))
            )
            regime_probs[regime] = likelihood
        
        # Normalize
        total = sum(regime_probs.values())
        if total > 0:
            regime_probs = {k: v/total for k, v in regime_probs.items()}
        else:
            regime_probs = {k: 1/len(MarketRegime) for k in MarketRegime}
        
        # Transition probabilities (based on history)
        transition_probs = self._estimate_transitions(current_regime)
        
        # Confidence based on probability concentration
        confidence = max(regime_probs.values())
        
        # Duration estimate
        duration = self._estimate_duration(current_regime)
        
        return RegimePrediction(
            current_regime=current_regime,
            regime_probabilities=regime_probs,
            transition_probabilities=transition_probs,
            confidence=confidence,
            duration_estimate=duration
        )
    
    def _estimate_transitions(
        self,
        current_regime: MarketRegime
    ) -> Dict[MarketRegime, float]:
        """Estimate transition probabilities from current regime"""
        
        if len(self.regime_history) < 2:
            return {r: 1/len(MarketRegime) for r in MarketRegime}
        
        # Count transitions from current regime
        transitions = {r: 0 for r in MarketRegime}
        total = 0
        
        for i in range(len(self.regime_history) - 1):
            if self.regime_history[i] == current_regime:
                transitions[self.regime_history[i + 1]] += 1
                total += 1
        
        if total > 0:
            return {k: v/total for k, v in transitions.items()}
        else:
            return {r: 1/len(MarketRegime) for r in MarketRegime}
    
    def _estimate_duration(self, regime: MarketRegime) -> int:
        """Estimate regime duration"""
        
        if len(self.regime_history) < 2:
            return 20
        
        # Find durations of this regime in history
        durations = []
        current_duration = 0
        
        for r in self.regime_history:
            if r == regime:
                current_duration += 1
            else:
                if current_duration > 0:
                    durations.append(current_duration)
                current_duration = 0
        
        if current_duration > 0:
            durations.append(current_duration)
        
        if durations:
            return int(np.mean(durations))
        else:
            return 20
    
    def get_regime_statistics(self) -> Dict[str, Any]:
        """Get regime statistics"""
        
        if not self.regime_history:
            return {'status': 'No history'}
        
        regime_counts = {}
        for r in MarketRegime:
            regime_counts[r.value] = sum(1 for h in self.regime_history if h == r)
        
        return {
            'total_observations': len(self.regime_history),
            'regime_distribution': regime_counts,
            'current_regime': self.regime_history[-1].value if self.regime_history else None
        }


# =============================================================================
# CAUSAL DISCOVERY FOR MARKET DYNAMICS
# =============================================================================

@dataclass
class CausalLink:
    """A discovered causal link"""
    cause: str
    effect: str
    lag: int
    strength: float
    confidence: float
    mechanism: str


class CausalDiscoveryEngine:
    """
    Causal Discovery for Market Dynamics
    
    Discovers causal relationships between market
    variables for better prediction.
    """
    
    def __init__(self, max_lag: int = 10):
        self.max_lag = max_lag
        self.discovered_links: List[CausalLink] = []
        self.causal_graph: Dict[str, List[CausalLink]] = {}
        
        logger.info("CausalDiscoveryEngine initialized")
    
    def pc_algorithm(
        self,
        data: Dict[str, np.ndarray],
        alpha: float = 0.05
    ) -> List[CausalLink]:
        """
        PC Algorithm for causal discovery
        
        Discovers causal structure from observational data.
        """
        
        variables = list(data.keys())
        n_vars = len(variables)
        
        # Start with fully connected graph
        adjacency = np.ones((n_vars, n_vars)) - np.eye(n_vars)
        
        # Remove edges based on conditional independence
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                var_i = data[variables[i]]
                var_j = data[variables[j]]
                
                # Test unconditional independence
                if len(var_i) == len(var_j) and len(var_i) > 10:
                    corr = np.corrcoef(var_i, var_j)[0, 1]
                    
                    if np.isfinite(corr):
                        # Fisher z-transform for significance
                        z = 0.5 * np.log((1 + corr) / (1 - corr + 1e-10))
                        se = 1 / np.sqrt(len(var_i) - 3)
                        p_value = 2 * (1 - self._normal_cdf(abs(z) / se))
                        
                        if p_value > alpha:
                            adjacency[i, j] = 0
                            adjacency[j, i] = 0
        
        # Convert to causal links
        links = []
        
        for i in range(n_vars):
            for j in range(n_vars):
                if adjacency[i, j] > 0 and i != j:
                    # Determine direction using time precedence
                    var_i = data[variables[i]]
                    var_j = data[variables[j]]
                    
                    best_lag, best_corr = self._find_best_lag(var_i, var_j)
                    
                    if best_lag > 0:  # i causes j
                        link = CausalLink(
                            cause=variables[i],
                            effect=variables[j],
                            lag=best_lag,
                            strength=abs(best_corr),
                            confidence=1 - self._correlation_p_value(best_corr, len(var_i)),
                            mechanism="temporal_precedence"
                        )
                        links.append(link)
        
        self.discovered_links.extend(links)
        
        # Build causal graph
        for link in links:
            if link.cause not in self.causal_graph:
                self.causal_graph[link.cause] = []
            self.causal_graph[link.cause].append(link)
        
        return links
    
    def _normal_cdf(self, x: float) -> float:
        """Standard normal CDF approximation"""
        return 0.5 * (1 + np.tanh(np.sqrt(2/np.pi) * (x + 0.044715 * x**3)))
    
    def _find_best_lag(
        self,
        cause: np.ndarray,
        effect: np.ndarray
    ) -> Tuple[int, float]:
        """Find lag with strongest correlation"""
        
        best_lag = 0
        best_corr = 0
        
        for lag in range(1, min(self.max_lag + 1, len(cause) // 3)):
            if lag < len(cause) and lag < len(effect):
                lagged_cause = cause[:-lag]
                aligned_effect = effect[lag:]
                
                if len(lagged_cause) == len(aligned_effect) and len(lagged_cause) > 10:
                    corr = np.corrcoef(lagged_cause, aligned_effect)[0, 1]
                    
                    if np.isfinite(corr) and abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = lag
        
        return best_lag, best_corr
    
    def _correlation_p_value(self, r: float, n: int) -> float:
        """Calculate p-value for correlation"""
        if n <= 2:
            return 1.0
        
        t = r * np.sqrt((n - 2) / (1 - r**2 + 1e-10))
        # Approximate p-value
        return 2 * (1 - self._normal_cdf(abs(t)))
    
    def transfer_entropy(
        self,
        source: np.ndarray,
        target: np.ndarray,
        lag: int = 1,
        bins: int = 10
    ) -> float:
        """
        Calculate transfer entropy from source to target
        
        Measures information flow between variables.
        """
        
        if len(source) != len(target) or len(source) < lag + 10:
            return 0.0
        
        # Discretize
        source_binned = np.digitize(source, np.linspace(source.min(), source.max(), bins))
        target_binned = np.digitize(target, np.linspace(target.min(), target.max(), bins))
        
        # Calculate joint and marginal probabilities
        n = len(source) - lag
        
        # P(target_t | target_t-1, source_t-1)
        # vs P(target_t | target_t-1)
        
        # Simplified: use correlation as proxy
        lagged_source = source[:-lag]
        lagged_target = target[:-lag]
        current_target = target[lag:]
        
        # Partial correlation
        corr_full = np.corrcoef(
            np.column_stack([lagged_source, lagged_target]).T,
            current_target
        )
        
        if corr_full.shape[0] >= 3:
            te = abs(corr_full[0, -1]) - abs(corr_full[1, -1])
            return max(0, te)
        
        return 0.0
    
    def discover_causal_structure(
        self,
        data: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Discover full causal structure"""
        
        # PC algorithm for structure
        links = self.pc_algorithm(data)
        
        # Transfer entropy for strength
        for link in links:
            if link.cause in data and link.effect in data:
                te = self.transfer_entropy(
                    data[link.cause],
                    data[link.effect],
                    link.lag
                )
                link.strength = max(link.strength, te)
        
        return {
            'num_links': len(links),
            'links': [
                {
                    'cause': l.cause,
                    'effect': l.effect,
                    'lag': l.lag,
                    'strength': l.strength,
                    'confidence': l.confidence
                }
                for l in links
            ],
            'graph_nodes': list(self.causal_graph.keys())
        }
    
    def predict_with_causes(
        self,
        target: str,
        data: Dict[str, np.ndarray]
    ) -> Optional[float]:
        """Predict target using discovered causes"""
        
        if target not in data:
            return None
        
        # Find causes of target
        causes = []
        for cause, links in self.causal_graph.items():
            for link in links:
                if link.effect == target:
                    causes.append((cause, link.lag, link.strength))
        
        if not causes:
            return None
        
        # Simple weighted prediction
        prediction = 0.0
        total_weight = 0.0
        
        for cause, lag, strength in causes:
            if cause in data and len(data[cause]) > lag:
                lagged_value = data[cause][-lag]
                prediction += strength * lagged_value
                total_weight += strength
        
        if total_weight > 0:
            return prediction / total_weight
        
        return None


# =============================================================================
# INTEGRATED PREDICTIVE SYSTEM
# =============================================================================

class IntegratedPredictiveSystem:
    """
    Integrated Predictive System
    
    Combines all predictive components for
    comprehensive forecasting.
    """
    
    def __init__(self):
        self.maintenance = PredictiveMaintenanceSystem()
        self.risk_prediction = RiskPredictionSystem()
        self.regime_predictor = MarketRegimePredictor()
        self.causal_discovery = CausalDiscoveryEngine()
        
        logger.info("IntegratedPredictiveSystem initialized")
    
    async def comprehensive_prediction(
        self,
        market_data: Dict[str, Any],
        system_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Generate comprehensive predictions"""
        
        results = {}
        
        # 1. System health prediction
        for component_id, metrics in system_metrics.items():
            if component_id not in self.maintenance.components:
                self.maintenance.register_component(component_id, component_id)
            self.maintenance.update_metrics(component_id, metrics)
        
        results['system_health'] = self.maintenance.get_system_health_report()
        
        # 2. Risk prediction
        if 'returns' in market_data:
            results['risk_alerts'] = self.risk_prediction.assess_risks(market_data)
        
        # 3. Regime prediction
        if 'returns' in market_data:
            regime_pred = self.regime_predictor.predict_regime(market_data['returns'])
            results['regime'] = {
                'current': regime_pred.current_regime.value,
                'confidence': regime_pred.confidence,
                'duration_estimate': regime_pred.duration_estimate
            }
        
        # 4. Causal analysis
        if len(market_data) > 1:
            causal_data = {k: v for k, v in market_data.items() if isinstance(v, np.ndarray)}
            if causal_data:
                results['causal_structure'] = self.causal_discovery.discover_causal_structure(causal_data)
        
        return results
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive predictive report"""
        
        return {
            'maintenance': self.maintenance.get_system_health_report(),
            'risk': self.risk_prediction.get_risk_dashboard(),
            'regime': self.regime_predictor.get_regime_statistics()
        }


# Convenience functions
def create_predictive_system() -> IntegratedPredictiveSystem:
    """Create integrated predictive system"""
    return IntegratedPredictiveSystem()
