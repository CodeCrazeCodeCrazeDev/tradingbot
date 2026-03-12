import logging
logger = logging.getLogger(__name__)
"""Explainable AI Module

This module provides natural language explanations for trading decisions,
model predictions, and risk assessments to enhance transparency and trust.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import json
from loguru import logger
from typing import Set
import numpy
import pandas


class ExplanationType(Enum):
    """Types of explanations."""
    TRADE_DECISION = auto()
    RISK_ASSESSMENT = auto()
    MODEL_PREDICTION = auto()
    MARKET_ANALYSIS = auto()
    STRATEGY_SELECTION = auto()


@dataclass
class Explanation:
    """AI explanation for a trading decision or analysis."""
    timestamp: datetime
    explanation_type: ExplanationType
    title: str
    summary: str
    detailed_explanation: str
    confidence: float  # 0.0 to 1.0
    key_factors: List[Dict[str, Any]]
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class ExplainableAI:
    """System for generating natural language explanations of AI decisions."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the explainable AI system.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_templates()
            logger.info("ExplainableAI system initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_templates(self):
        """Initialize explanation templates."""
        try:
            self.templates = {
                "trade_decision": {
                    "buy": "Recommending BUY for {symbol} based on {primary_reason}. {confidence_text}",
                    "sell": "Recommending SELL for {symbol} based on {primary_reason}. {confidence_text}",
                    "hold": "Recommending HOLD for {symbol} due to {primary_reason}. {confidence_text}"
                },
                "risk_assessment": {
                    "low": "Risk level is LOW for {symbol}. {risk_factors}",
                    "medium": "Risk level is MEDIUM for {symbol}. {risk_factors}",
                    "high": "Risk level is HIGH for {symbol}. {risk_factors}"
                },
                "confidence_levels": {
                    "very_high": "Very high confidence (>90%)",
                    "high": "High confidence (70-90%)",
                    "medium": "Medium confidence (50-70%)",
                    "low": "Low confidence (<50%)"
                }
            }
        except Exception as e:
            logger.error(f"Error in _init_templates: {e}")
            raise
    
    def explain_trade_decision(self, 
                             symbol: str,
                             decision: str,  # 'buy', 'sell', 'hold'
                             model_output: Dict[str, Any],
                             market_data: Dict[str, Any],
                             confidence: float) -> Explanation:
        """Generate explanation for a trade decision.
        
        Args:
            symbol: Trading symbol
            decision: Trade decision ('buy', 'sell', 'hold')
            model_output: Model prediction output
            market_data: Current market data
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Explanation object
        """
        # Analyze key factors
        try:
            key_factors = self._analyze_decision_factors(model_output, market_data)
        
            # Get primary reason
            primary_factor = max(key_factors, key=lambda x: x['importance']) if key_factors else None
            primary_reason = primary_factor['description'] if primary_factor else "mixed signals"
        
            # Generate confidence text
            confidence_text = self._get_confidence_text(confidence)
        
            # Create summary
            summary = self.templates["trade_decision"][decision].format(
                symbol=symbol,
                primary_reason=primary_reason,
                confidence_text=confidence_text
            )
        
            # Generate detailed explanation
            detailed_explanation = self._generate_detailed_trade_explanation(
                symbol, decision, key_factors, market_data, confidence
            )
        
            # Generate recommendations
            recommendations = self._generate_trade_recommendations(decision, key_factors, confidence)
        
            return Explanation(
                timestamp=datetime.now(),
                explanation_type=ExplanationType.TRADE_DECISION,
                title=f"Trade Decision: {decision.upper()} {symbol}",
                summary=summary,
                detailed_explanation=detailed_explanation,
                confidence=confidence,
                key_factors=key_factors,
                supporting_data={
                    "symbol": symbol,
                    "decision": decision,
                    "model_output": model_output,
                    "market_data": market_data
                },
                recommendations=recommendations
            )
        except Exception as e:
            logger.error(f"Error in explain_trade_decision: {e}")
            raise
    
    def explain_risk_assessment(self,
                              symbol: str,
                              risk_level: str,  # 'low', 'medium', 'high'
                              risk_metrics: Dict[str, Any],
                              market_conditions: Dict[str, Any]) -> Explanation:
        """Generate explanation for risk assessment.
        
        Args:
            symbol: Trading symbol
            risk_level: Risk level assessment
            risk_metrics: Risk calculation metrics
            market_conditions: Current market conditions
            
        Returns:
            Explanation object
        """
        # Analyze risk factors
        try:
            risk_factors = self._analyze_risk_factors(risk_metrics, market_conditions)
        
            # Create risk factors text
            risk_factors_text = self._format_risk_factors(risk_factors)
        
            # Create summary
            summary = self.templates["risk_assessment"][risk_level].format(
                symbol=symbol,
                risk_factors=risk_factors_text
            )
        
            # Generate detailed explanation
            detailed_explanation = self._generate_detailed_risk_explanation(
                symbol, risk_level, risk_factors, market_conditions
            )
        
            # Calculate confidence based on risk metric consistency
            confidence = self._calculate_risk_confidence(risk_factors)
        
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_level, risk_factors)
        
            return Explanation(
                timestamp=datetime.now(),
                explanation_type=ExplanationType.RISK_ASSESSMENT,
                title=f"Risk Assessment: {risk_level.upper()} for {symbol}",
                summary=summary,
                detailed_explanation=detailed_explanation,
                confidence=confidence,
                key_factors=risk_factors,
                supporting_data={
                    "symbol": symbol,
                    "risk_level": risk_level,
                    "risk_metrics": risk_metrics,
                    "market_conditions": market_conditions
                },
                recommendations=recommendations
            )
        except Exception as e:
            logger.error(f"Error in explain_risk_assessment: {e}")
            raise
    
    def explain_model_prediction(self,
                               model_name: str,
                               prediction: Any,
                               feature_importance: Dict[str, float],
                               input_data: Dict[str, Any]) -> Explanation:
        """Generate explanation for model prediction.
        
        Args:
            model_name: Name of the model
            prediction: Model prediction
            feature_importance: Feature importance scores
            input_data: Input data used for prediction
            
        Returns:
            Explanation object
        """
        # Analyze feature contributions
        try:
            key_factors = self._analyze_feature_importance(feature_importance, input_data)
        
            # Generate prediction summary
            prediction_text = self._format_prediction(prediction)
            summary = f"Model {model_name} predicts {prediction_text} based on {len(key_factors)} key factors"
        
            # Generate detailed explanation
            detailed_explanation = self._generate_model_explanation(
                model_name, prediction, key_factors, input_data
            )
        
            # Calculate confidence based on feature importance distribution
            confidence = self._calculate_model_confidence(feature_importance)
        
            # Generate recommendations
            recommendations = self._generate_model_recommendations(prediction, key_factors)
        
            return Explanation(
                timestamp=datetime.now(),
                explanation_type=ExplanationType.MODEL_PREDICTION,
                title=f"Model Prediction: {model_name}",
                summary=summary,
                detailed_explanation=detailed_explanation,
                confidence=confidence,
                key_factors=key_factors,
                supporting_data={
                    "model_name": model_name,
                    "prediction": prediction,
                    "feature_importance": feature_importance,
                    "input_data": input_data
                },
                recommendations=recommendations
            )
        except Exception as e:
            logger.error(f"Error in explain_model_prediction: {e}")
            raise
    
    def _analyze_decision_factors(self, 
                                model_output: Dict[str, Any],
                                market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze factors contributing to trade decision."""
        try:
            factors = []
        
            # Technical indicators
            if 'technical_signals' in model_output:
                tech_signals = model_output['technical_signals']
                for signal, value in tech_signals.items():
                    if abs(value) > 0.3:  # Significant signal
                        factors.append({
                            'name': signal,
                            'value': value,
                            'importance': abs(value),
                            'description': f"{signal} indicates {'bullish' if value > 0 else 'bearish'} momentum",
                            'category': 'technical'
                        })
        
            # Market conditions
            if 'market_regime' in market_data:
                regime = market_data['market_regime']
                factors.append({
                    'name': 'market_regime',
                    'value': regime,
                    'importance': 0.8,
                    'description': f"Market is in {regime} regime",
                    'category': 'market'
                })
        
            # Volume analysis
            if 'volume_ratio' in market_data:
                vol_ratio = market_data['volume_ratio']
                if vol_ratio > 1.5 or vol_ratio < 0.5:
                    factors.append({
                        'name': 'volume',
                        'value': vol_ratio,
                        'importance': min(1.0, abs(vol_ratio - 1.0)),
                        'description': f"Volume is {'above' if vol_ratio > 1 else 'below'} average",
                        'category': 'volume'
                    })
        
            # Sort by importance
            factors.sort(key=lambda x: x['importance'], reverse=True)
            return factors[:5]  # Top 5 factors
        except Exception as e:
            logger.error(f"Error in _analyze_decision_factors: {e}")
            raise
    
    def _analyze_risk_factors(self,
                            risk_metrics: Dict[str, Any],
                            market_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze risk factors."""
        try:
            factors = []
        
            # Volatility
            if 'volatility' in risk_metrics:
                vol = risk_metrics['volatility']
                if vol > 0.02:  # High volatility threshold
                    factors.append({
                        'name': 'volatility',
                        'value': vol,
                        'importance': min(1.0, vol * 20),
                        'description': f"High volatility ({vol:.2%}) increases risk",
                        'category': 'volatility'
                    })
        
            # Drawdown
            if 'max_drawdown' in risk_metrics:
                dd = risk_metrics['max_drawdown']
                if abs(dd) > 0.05:  # Significant drawdown
                    factors.append({
                        'name': 'drawdown',
                        'value': dd,
                        'importance': min(1.0, abs(dd) * 10),
                        'description': f"Recent drawdown of {dd:.2%}",
                        'category': 'performance'
                    })
        
            # Market stress
            if 'market_stress' in market_conditions:
                stress = market_conditions['market_stress']
                if stress > 0.5:
                    factors.append({
                        'name': 'market_stress',
                        'value': stress,
                        'importance': stress,
                        'description': f"Market stress level is {stress:.1%}",
                        'category': 'market'
                    })
        
            factors.sort(key=lambda x: x['importance'], reverse=True)
            return factors
        except Exception as e:
            logger.error(f"Error in _analyze_risk_factors: {e}")
            raise
    
    def _analyze_feature_importance(self,
                                  feature_importance: Dict[str, float],
                                  input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze feature importance for model explanation."""
        try:
            factors = []
        
            for feature, importance in feature_importance.items():
                if importance > 0.1:  # Significant importance
                    value = input_data.get(feature, 'N/A')
                    factors.append({
                        'name': feature,
                        'value': value,
                        'importance': importance,
                        'description': f"{feature} contributes {importance:.1%} to prediction",
                        'category': 'feature'
                    })
        
            factors.sort(key=lambda x: x['importance'], reverse=True)
            return factors[:10]  # Top 10 features
        except Exception as e:
            logger.error(f"Error in _analyze_feature_importance: {e}")
            raise
    
    def _generate_detailed_trade_explanation(self,
                                           symbol: str,
                                           decision: str,
                                           key_factors: List[Dict[str, Any]],
                                           market_data: Dict[str, Any],
                                           confidence: float) -> str:
        """Generate detailed trade explanation."""
        try:
            explanation = f"Analysis for {symbol} ({decision.upper()}):\n\n"
        
            explanation += f"Decision Confidence: {confidence:.1%}\n\n"
        
            explanation += "Key Contributing Factors:\n"
            for i, factor in enumerate(key_factors[:3], 1):
                explanation += f"{i}. {factor['description']} (Weight: {factor['importance']:.1%})\n"
        
            explanation += f"\nMarket Context:\n"
            if 'price' in market_data:
                explanation += f"- Current Price: {market_data['price']}\n"
            if 'trend' in market_data:
                explanation += f"- Trend Direction: {market_data['trend']}\n"
        
            return explanation
        except Exception as e:
            logger.error(f"Error in _generate_detailed_trade_explanation: {e}")
            raise
    
    def _generate_detailed_risk_explanation(self,
                                          symbol: str,
                                          risk_level: str,
                                          risk_factors: List[Dict[str, Any]],
                                          market_conditions: Dict[str, Any]) -> str:
        """Generate detailed risk explanation."""
        try:
            explanation = f"Risk Assessment for {symbol}: {risk_level.upper()}\n\n"
        
            explanation += "Primary Risk Factors:\n"
            for i, factor in enumerate(risk_factors[:3], 1):
                explanation += f"{i}. {factor['description']}\n"
        
            explanation += f"\nRisk Mitigation Suggestions:\n"
            if risk_level == 'high':
                explanation += "- Consider reducing position size\n"
                explanation += "- Implement tighter stop losses\n"
                explanation += "- Monitor positions more frequently\n"
            elif risk_level == 'medium':
                explanation += "- Maintain standard risk controls\n"
                explanation += "- Monitor key risk metrics\n"
            else:
                explanation += "- Standard position sizing acceptable\n"
                explanation += "- Continue regular monitoring\n"
        
            return explanation
        except Exception as e:
            logger.error(f"Error in _generate_detailed_risk_explanation: {e}")
            raise
    
    def _generate_model_explanation(self,
                                  model_name: str,
                                  prediction: Any,
                                  key_factors: List[Dict[str, Any]],
                                  input_data: Dict[str, Any]) -> str:
        """Generate detailed model explanation."""
        try:
            explanation = f"Model: {model_name}\n"
            explanation += f"Prediction: {self._format_prediction(prediction)}\n\n"
        
            explanation += "Most Important Features:\n"
            for i, factor in enumerate(key_factors[:5], 1):
                explanation += f"{i}. {factor['name']}: {factor['value']} "
                explanation += f"(Importance: {factor['importance']:.1%})\n"
        
            explanation += f"\nModel Interpretation:\n"
            explanation += f"The model analyzed {len(input_data)} input features "
            explanation += f"and identified {len(key_factors)} significant contributors to this prediction.\n"
        
            return explanation
        except Exception as e:
            logger.error(f"Error in _generate_model_explanation: {e}")
            raise
    
    def _get_confidence_text(self, confidence: float) -> str:
        """Get confidence level text."""
        try:
            if confidence >= 0.9:
                return self.templates["confidence_levels"]["very_high"]
            elif confidence >= 0.7:
                return self.templates["confidence_levels"]["high"]
            elif confidence >= 0.5:
                return self.templates["confidence_levels"]["medium"]
            else:
                return self.templates["confidence_levels"]["low"]
        except Exception as e:
            logger.error(f"Error in _get_confidence_text: {e}")
            raise
    
    def _format_risk_factors(self, risk_factors: List[Dict[str, Any]]) -> str:
        """Format risk factors for display."""
        try:
            if not risk_factors:
                return "No significant risk factors identified"
        
            primary_factor = risk_factors[0]
            return primary_factor['description']
        except Exception as e:
            logger.error(f"Error in _format_risk_factors: {e}")
            raise
    
    def _format_prediction(self, prediction: Any) -> str:
        """Format prediction for display."""
        try:
            if isinstance(prediction, (int, float)):
                return f"{prediction:.4f}"
            elif isinstance(prediction, str):
                return prediction
            else:
                return str(prediction)
        except Exception as e:
            logger.error(f"Error in _format_prediction: {e}")
            raise
    
    def _calculate_risk_confidence(self, risk_factors: List[Dict[str, Any]]) -> float:
        """Calculate confidence in risk assessment."""
        try:
            if not risk_factors:
                return 0.5
        
            # Higher confidence when factors are consistent
            importances = [f['importance'] for f in risk_factors]
            if importances:
                return min(1.0, np.mean(importances) + 0.2)
            return 0.5
        except Exception as e:
            logger.error(f"Error in _calculate_risk_confidence: {e}")
            raise
    
    def _calculate_model_confidence(self, feature_importance: Dict[str, float]) -> float:
        """Calculate confidence in model prediction."""
        try:
            if not feature_importance:
                return 0.5
        
            # Higher confidence when feature importance is concentrated
            importances = list(feature_importance.values())
            if importances:
                top_features_importance = sum(sorted(importances, reverse=True)[:3])
                return min(1.0, top_features_importance)
            return 0.5
        except Exception as e:
            logger.error(f"Error in _calculate_model_confidence: {e}")
            raise
    
    def _generate_trade_recommendations(self,
                                      decision: str,
                                      key_factors: List[Dict[str, Any]],
                                      confidence: float) -> List[str]:
        """Generate trade recommendations."""
        try:
            recommendations = []
        
            if confidence < 0.6:
                recommendations.append("Consider waiting for stronger signals before acting")
        
            if decision in ['buy', 'sell']:
                recommendations.append("Set appropriate stop-loss levels")
                recommendations.append("Monitor key technical levels")
        
            # Factor-specific recommendations
            for factor in key_factors[:2]:
                if factor['category'] == 'technical':
                    recommendations.append(f"Watch {factor['name']} for confirmation")
                elif factor['category'] == 'volume':
                    recommendations.append("Monitor volume for trend confirmation")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_trade_recommendations: {e}")
            raise
    
    def _generate_risk_recommendations(self,
                                     risk_level: str,
                                     risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate risk management recommendations."""
        try:
            recommendations = []
        
            if risk_level == 'high':
                recommendations.extend([
                    "Reduce position size by 25-50%",
                    "Implement tighter stop-losses",
                    "Increase monitoring frequency"
                ])
            elif risk_level == 'medium':
                recommendations.extend([
                    "Maintain standard position sizing",
                    "Keep current stop-loss levels",
                    "Monitor risk metrics regularly"
                ])
            else:
                recommendations.extend([
                    "Standard risk management applies",
                    "Consider slightly larger positions if appropriate"
                ])
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_risk_recommendations: {e}")
            raise
    
    def _generate_model_recommendations(self,
                                      prediction: Any,
                                      key_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate model-based recommendations."""
        try:
            recommendations = []
        
            recommendations.append("Validate prediction with additional analysis")
            recommendations.append("Monitor key input features for changes")
        
            if key_factors:
                top_factor = key_factors[0]
                recommendations.append(f"Pay special attention to {top_factor['name']}")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_model_recommendations: {e}")
            raise
    
    def generate_summary_report(self, explanations: List[Explanation]) -> str:
        """Generate a summary report of multiple explanations."""
        try:
            if not explanations:
                return "No explanations available."
        
            report = "AI Decision Summary Report\n"
            report += "=" * 30 + "\n\n"
        
            # Group by type
            by_type = {}
            for exp in explanations:
                exp_type = exp.explanation_type.name
                if exp_type not in by_type:
                    by_type[exp_type] = []
                by_type[exp_type].append(exp)
        
            for exp_type, exp_list in by_type.items():
                report += f"{exp_type.replace('_', ' ').title()}:\n"
                for exp in exp_list:
                    report += f"- {exp.title}: {exp.summary}\n"
                report += "\n"
        
            # Overall confidence
            avg_confidence = np.mean([exp.confidence for exp in explanations])
            report += f"Overall Confidence: {avg_confidence:.1%}\n"
        
            return report
        except Exception as e:
            logger.error(f"Error in generate_summary_report: {e}")
            raise
