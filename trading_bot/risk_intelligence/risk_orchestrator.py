"""
Risk Intelligence Orchestrator
==============================

Aggregates all risk signals into unified risk dashboard.

Outputs:
- Current risk level (1-10)
- Position sizing multiplier (0.0 - 1.0)
- Kill switch triggers (emergency liquidation conditions)
- Correlation stress scenarios
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import logging

from .liquidity_trap_detector import LiquidityTrapDetector, LiquidityRisk
from .manipulation_detector import MarketManipulationDetector, ManipulationAlert
from .regime_shift_predictor import RegimeShiftPredictor, RegimePrediction
from .volatility_explosion_forecaster import VolatilityExplosionForecaster, VolatilityForecast

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels from 1-10."""
    CRITICAL = 10
    SEVERE = 8
    HIGH = 6
    ELEVATED = 4
    MODERATE = 3
    LOW = 1
    MINIMAL = 0


@dataclass
class RiskDashboard:
    """Unified risk dashboard."""
    timestamp: datetime
    overall_risk_level: RiskLevel
    risk_score: float  # 0.0-1.0
    
    # Component risks
    liquidity_risk: float
    manipulation_risk: float
    regime_risk: float
    volatility_risk: float
    
    # Actionable outputs
    position_size_multiplier: float  # 0.0-1.0
    kill_switch_triggered: bool
    kill_switch_reason: str
    
    # Active alerts
    active_alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'overall_risk_level': self.overall_risk_level.name,
            'risk_score': self.risk_score,
            'liquidity_risk': self.liquidity_risk,
            'manipulation_risk': self.manipulation_risk,
            'regime_risk': self.regime_risk,
            'volatility_risk': self.volatility_risk,
            'position_size_multiplier': self.position_size_multiplier,
            'kill_switch_triggered': self.kill_switch_triggered,
            'kill_switch_reason': self.kill_switch_reason,
            'active_alerts': self.active_alerts,
            'recommended_actions': self.recommended_actions,
        }


class RiskIntelligenceOrchestrator:
    """
    Central orchestrator for all risk intelligence.
    
    Aggregates signals from 4 risk detectors into unified dashboard
    with position sizing recommendations and kill switch triggers.
    """
    
    def __init__(self,
                 liquidity_detector: Optional[LiquidityTrapDetector] = None,
                 manipulation_detector: Optional[MarketManipulationDetector] = None,
                 regime_predictor: Optional[RegimeShiftPredictor] = None,
                 volatility_forecaster: Optional[VolatilityExplosionForecaster] = None):
        """
        Initialize orchestrator with risk detectors.
        
        Args:
            liquidity_detector: Liquidity trap detector
            manipulation_detector: Manipulation detector
            regime_predictor: Regime shift predictor
            volatility_forecaster: Volatility forecaster
        """
        self.liquidity_detector = liquidity_detector or LiquidityTrapDetector()
        self.manipulation_detector = manipulation_detector or MarketManipulationDetector()
        self.regime_predictor = regime_predictor or RegimeShiftPredictor()
        self.volatility_forecaster = volatility_forecaster or VolatilityExplosionForecaster()
        
        # Risk thresholds
        self.kill_switch_threshold = 0.9  # Critical risk triggers kill
        self.high_risk_threshold = 0.7
        self.elevated_risk_threshold = 0.5
        
        # History
        self.risk_history: List[RiskDashboard] = []
        self.max_history = 1000
        
        logger.info("RiskIntelligenceOrchestrator initialized")
    
    def update_risk_assessment(self,
                              asset: str,
                              current_spread: float,
                              current_depth: float,
                              returns: List[float],
                              asset_returns: Optional[Dict[str, List[float]]] = None,
                              macro_indicators: Optional[Dict[str, float]] = None,
                              current_vix: Optional[float] = None) -> RiskDashboard:
        """
        Update comprehensive risk assessment.
        
        Args:
            asset: Primary asset being traded
            current_spread: Current bid-ask spread
            current_depth: Current order book depth
            returns: Price returns
            asset_returns: Multi-asset returns for correlation analysis
            macro_indicators: Macro indicators
            current_vix: Current VIX level
            
        Returns:
            RiskDashboard
        """
        timestamp = datetime.now()
        active_alerts = []
        
        # Check liquidity risk
        liquidity_risk = self._assess_liquidity_risk(
            asset, current_spread, current_depth
        )
        
        # Check manipulation risk
        manipulation_risk = self._assess_manipulation_risk(asset)
        
        # Check regime risk
        regime_risk = self._assess_regime_risk(
            returns, asset_returns or {}, macro_indicators or {}
        )
        
        # Check volatility risk
        volatility_risk = self._assess_volatility_risk(returns, current_vix)
        
        # Aggregate risk components
        risk_components = {
            'liquidity': liquidity_risk,
            'manipulation': manipulation_risk,
            'regime': regime_risk,
            'volatility': volatility_risk,
        }
        
        # Calculate overall risk score (weighted)
        weights = {
            'liquidity': 0.25,
            'manipulation': 0.20,
            'regime': 0.30,
            'volatility': 0.25,
        }
        
        risk_score = sum(risk_components[k] * weights[k] for k in risk_components)
        
        # Determine risk level
        overall_risk = self._score_to_risk_level(risk_score)
        
        # Determine kill switch
        kill_switch, kill_reason = self._check_kill_switch(
            risk_score, risk_components, active_alerts
        )
        
        # Calculate position size multiplier
        position_multiplier = self._calculate_position_multiplier(
            risk_score, overall_risk, kill_switch
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_components, overall_risk, kill_switch
        )
        
        dashboard = RiskDashboard(
            timestamp=timestamp,
            overall_risk_level=overall_risk,
            risk_score=risk_score,
            liquidity_risk=risk_components['liquidity'],
            manipulation_risk=risk_components['manipulation'],
            regime_risk=risk_components['regime'],
            volatility_risk=risk_components['volatility'],
            position_size_multiplier=position_multiplier,
            kill_switch_triggered=kill_switch,
            kill_switch_reason=kill_reason,
            active_alerts=active_alerts,
            recommended_actions=recommendations,
        )
        
        # Store history
        self.risk_history.append(dashboard)
        if len(self.risk_history) > self.max_history:
            self.risk_history = self.risk_history[-self.max_history:]
        
        return dashboard
    
    def _assess_liquidity_risk(self, asset: str, 
                              current_spread: float,
                              current_depth: float) -> float:
        """Assess liquidity risk (0.0-1.0)."""
        risk = self.liquidity_detector.detect(asset, current_spread, current_depth)
        
        if risk is None:
            return 0.1  # Low baseline risk
        
        return risk.risk_level
    
    def _assess_manipulation_risk(self, asset: str) -> float:
        """Assess manipulation risk (0.0-1.0)."""
        # Check historical alerts
        summary = self.manipulation_detector.get_manipulation_summary(asset)
        
        base_risk = 0.05  # Low baseline
        
        if summary.get('recent_alerts', 0) > 0:
            base_risk = 0.3
        
        return min(1.0, base_risk)
    
    def _assess_regime_risk(self,
                           returns: List[float],
                           asset_returns: Dict[str, List[float]],
                           macro_indicators: Dict[str, float]) -> float:
        """Assess regime shift risk (0.0-1.0)."""
        prediction = self.regime_predictor.get_composite_prediction(
            returns, asset_returns, macro_indicators
        )
        
        if prediction is None:
            return 0.15  # Baseline regime uncertainty
        
        # Higher risk if predicting crisis or high volatility
        if prediction.predicted_regime.value in ['crisis', 'high_volatility']:
            return prediction.confidence
        
        return prediction.confidence * 0.3
    
    def _assess_volatility_risk(self,
                               returns: List[float],
                               current_vix: Optional[float]) -> float:
        """Assess volatility explosion risk (0.0-1.0)."""
        forecast = self.volatility_forecaster.forecast_garch(returns)
        
        if forecast is None:
            return 0.2  # Baseline vol risk
        
        # Risk based on spike probability
        return min(1.0, forecast.probability_of_spike * 1.5)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert risk score to risk level."""
        if score >= 0.9:
            return RiskLevel.CRITICAL
        elif score >= 0.8:
            return RiskLevel.SEVERE
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.ELEVATED
        elif score >= 0.2:
            return RiskLevel.MODERATE
        elif score >= 0.05:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL
    
    def _check_kill_switch(self, 
                          risk_score: float,
                          risk_components: Dict[str, float],
                          active_alerts: List[Dict]) -> Tuple[bool, str]:
        """Check if kill switch should be triggered."""
        if risk_score >= self.kill_switch_threshold:
            return True, f"Critical risk level: {risk_score:.1%}"
        
        # Check for multiple severe risks
        severe_count = sum(1 for v in risk_components.values() if v > 0.8)
        if severe_count >= 2:
            return True, f"Multiple severe risks: {severe_count} components > 80%"
        
        # Check for liquidity trap + high volatility
        if risk_components['liquidity'] > 0.8 and risk_components['volatility'] > 0.7:
            return True, "Liquidity trap with high volatility"
        
        # Check for manipulation + high regime risk
        if risk_components['manipulation'] > 0.6 and risk_components['regime'] > 0.8:
            return True, "Manipulation detected during regime transition"
        
        return False, ""
    
    def _calculate_position_multiplier(self,
                                      risk_score: float,
                                      risk_level: RiskLevel,
                                      kill_switch: bool) -> float:
        """Calculate position size multiplier based on risk."""
        if kill_switch:
            return 0.0  # Emergency exit
        
        # Base multiplier from risk score
        base_multiplier = max(0.0, 1.0 - risk_score)
        
        # Adjust for risk level
        level_multipliers = {
            RiskLevel.CRITICAL: 0.0,
            RiskLevel.SEVERE: 0.1,
            RiskLevel.HIGH: 0.25,
            RiskLevel.ELEVATED: 0.5,
            RiskLevel.MODERATE: 0.75,
            RiskLevel.LOW: 0.9,
            RiskLevel.MINIMAL: 1.0,
        }
        
        level_multiplier = level_multipliers.get(risk_level, 1.0)
        
        # Take the more conservative
        return min(base_multiplier, level_multiplier)
    
    def _generate_recommendations(self,
                                 risk_components: Dict[str, float],
                                 risk_level: RiskLevel,
                                 kill_switch: bool) -> List[str]:
        """Generate recommended actions based on risk assessment."""
        recommendations = []
        
        if kill_switch:
            recommendations.append("IMMEDIATE: Liquidate all positions")
            recommendations.append("Suspend trading until risk subsides")
            return recommendations
        
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.SEVERE]:
            recommendations.append("Reduce position sizes by 75% or more")
            recommendations.append("Implement tight stop-losses")
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.ELEVATED]:
            recommendations.append("Reduce position sizes by 50%")
            recommendations.append("Monitor risk dashboard closely")
        
        if risk_components['liquidity'] > 0.6:
            recommendations.append("Avoid entering new positions - liquidity constrained")
        
        if risk_components['manipulation'] > 0.5:
            recommendations.append("Exercise caution - manipulation signals detected")
        
        if risk_components['volatility'] > 0.7:
            recommendations.append("Prepare for volatility expansion - reduce leverage")
        
        if not recommendations:
            recommendations.append("Risk levels acceptable - maintain normal operations")
        
        return recommendations
    
    def get_risk_trend(self, hours: int = 24) -> Dict[str, Any]:
        """Get risk trend over specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [r for r in self.risk_history if r.timestamp > cutoff]
        
        if not recent:
            return {'status': 'insufficient_data'}
        
        risk_scores = [r.risk_score for r in recent]
        
        return {
            'period_hours': hours,
            'current_risk': risk_scores[-1],
            'avg_risk': np.mean(risk_scores),
            'max_risk': max(risk_scores),
            'min_risk': min(risk_scores),
            'trend': 'increasing' if risk_scores[-1] > risk_scores[0] else 'decreasing',
            'kill_switches_triggered': sum(1 for r in recent if r.kill_switch_triggered),
        }
