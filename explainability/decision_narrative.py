"""
Phase 7: Explainability - Natural Language Explanations
Generates human-readable explanations of trading decisions
"""

import torch
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DecisionNarrator:
    """
    Generates natural language explanations of trading decisions.
    Combines multiple factors into coherent narrative.
    """
    
    def __init__(self):
        # Templates for different aspects
        self.templates = {
            'decision': {
                'BUY': "Recommending to BUY {symbol} based on {reasons}",
                'SELL': "Recommending to SELL {symbol} based on {reasons}",
                'HOLD': "Recommending to HOLD {symbol} because {reasons}"
            },
            'confidence': {
                'high': "Very confident in this decision ({confidence:.1%})",
                'medium': "Moderately confident ({confidence:.1%})",
                'low': "Low confidence decision ({confidence:.1%})"
            },
            'trend': {
                'strong_up': "Strong upward trend detected",
                'weak_up': "Weak upward trend",
                'strong_down': "Strong downward trend",
                'weak_down': "Weak downward trend",
                'sideways': "Market moving sideways"
            },
            'risk': {
                'high': "High risk environment",
                'medium': "Moderate risk levels",
                'low': "Low risk conditions"
            }
        }
        
        logger.info("✅ Decision Narrator initialized")
    
    def explain_decision(
        self,
        decision: str,
        symbol: str,
        confidence: float,
        analysis: Dict,
        attributions: Optional[Dict] = None
    ) -> str:
        """
        Generate complete decision explanation.
        
        Args:
            decision: Trading decision (BUY/SELL/HOLD)
            symbol: Trading symbol
            confidence: Decision confidence
            analysis: Analysis results
            attributions: Optional feature attributions
        
        Returns:
            Natural language explanation
        """
        # Build explanation components
        components = []
        
        # 1. Main decision
        reasons = self._get_decision_reasons(analysis)
        components.append(self.templates['decision'][decision].format(
            symbol=symbol,
            reasons=reasons
        ))
        
        # 2. Confidence level
        conf_level = self._get_confidence_level(confidence)
        components.append(self.templates['confidence'][conf_level].format(
            confidence=confidence
        ))
        
        # 3. Technical Analysis
        components.extend(self._explain_technical_analysis(analysis))
        
        # 4. Risk Assessment
        components.extend(self._explain_risk_analysis(analysis))
        
        # 5. Feature Attributions
        if attributions:
            components.extend(self._explain_attributions(attributions))
        
        # 6. Market Context
        components.extend(self._explain_market_context(analysis))
        
        # Combine all components
        explanation = "\n\n".join(components)
        
        # Add timestamp
        explanation += f"\n\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return explanation
    
    def _get_decision_reasons(self, analysis: Dict) -> str:
        """Extract main reasons for decision."""
        reasons = []
        
        # Technical signals
        if 'technical' in analysis:
            tech = analysis['technical']
            if tech.get('trend_strength', 0) > 0.7:
                reasons.append("strong technical trend")
            if tech.get('momentum', 0) > 0.5:
                reasons.append("positive momentum")
        
        # Sentiment
        if 'sentiment' in analysis:
            sent = analysis['sentiment']
            if abs(sent.get('overall', 0)) > 0.5:
                direction = "positive" if sent['overall'] > 0 else "negative"
                reasons.append(f"{direction} market sentiment")
        
        # Risk
        if 'risk' in analysis:
            risk = analysis['risk']
            if risk.get('level', 'medium') == 'low':
                reasons.append("favorable risk conditions")
        
        if not reasons:
            reasons.append("multiple technical and fundamental factors")
        
        return ", ".join(reasons)
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Determine confidence level."""
        if confidence > 0.8:
            return 'high'
        elif confidence > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _explain_technical_analysis(self, analysis: Dict) -> List[str]:
        """Generate technical analysis explanation."""
        explanations = ["Technical Analysis:"]
        
        if 'technical' in analysis:
            tech = analysis['technical']
            
            # Trend
            trend_strength = tech.get('trend_strength', 0)
            trend_direction = tech.get('trend_direction', 'sideways')
            
            if trend_strength > 0.7:
                if trend_direction == 'up':
                    explanations.append("- " + self.templates['trend']['strong_up'])
                elif trend_direction == 'down':
                    explanations.append("- " + self.templates['trend']['strong_down'])
            elif trend_strength > 0.3:
                if trend_direction == 'up':
                    explanations.append("- " + self.templates['trend']['weak_up'])
                elif trend_direction == 'down':
                    explanations.append("- " + self.templates['trend']['weak_down'])
            else:
                explanations.append("- " + self.templates['trend']['sideways'])
            
            # Indicators
            if 'indicators' in tech:
                ind = tech['indicators']
                explanations.append(f"- RSI: {ind.get('rsi', 0):.1f}")
                explanations.append(f"- MACD: {ind.get('macd', 0):.4f}")
            
            # Support/Resistance
            if 'levels' in tech:
                levels = tech['levels']
                explanations.append(
                    f"- Support: {levels.get('support', 0):.4f}"
                )
                explanations.append(
                    f"- Resistance: {levels.get('resistance', 0):.4f}"
                )
        
        return explanations
    
    def _explain_risk_analysis(self, analysis: Dict) -> List[str]:
        """Generate risk analysis explanation."""
        explanations = ["Risk Analysis:"]
        
        if 'risk' in analysis:
            risk = analysis['risk']
            
            # Risk level
            level = risk.get('level', 'medium')
            explanations.append("- " + self.templates['risk'][level])
            
            # Volatility
            vol = risk.get('volatility', 0)
            explanations.append(f"- Volatility: {vol:.1%}")
            
            # Position sizing
            size = risk.get('position_size', 0)
            explanations.append(f"- Recommended position size: {size:.1%}")
            
            # Stop loss
            sl = risk.get('stop_loss', 0)
            if sl > 0:
                explanations.append(f"- Stop loss: {sl:.1%}")
        
        return explanations
    
    def _explain_attributions(self, attributions: Dict) -> List[str]:
        """Generate feature attribution explanation."""
        explanations = ["Feature Importance:"]
        
        if 'analysis' in attributions:
            analysis = attributions['analysis']
            
            # Top features
            if 'top_features' in analysis:
                for feature in analysis['top_features'][:3]:  # Top 3
                    impact = "positive" if feature['attribution'] > 0 else "negative"
                    explanations.append(
                        f"- {feature['feature']}: {impact} impact "
                        f"(importance: {feature['importance']:.3f})"
                    )
            
            # Feature types
            if 'importance_by_type' in analysis:
                explanations.append("\nFeature Types:")
                for ftype, importance in analysis['importance_by_type'].items():
                    explanations.append(f"- {ftype}: {importance:.3f}")
        
        return explanations
    
    def _explain_market_context(self, analysis: Dict) -> List[str]:
        """Generate market context explanation."""
        explanations = ["Market Context:"]
        
        if 'context' in analysis:
            context = analysis['context']
            
            # Market regime
            if 'regime' in context:
                explanations.append(f"- Market Regime: {context['regime']}")
            
            # Sentiment
            if 'sentiment' in context:
                sent = context['sentiment']
                explanations.append(
                    f"- Market Sentiment: {sent.get('overall', 0):.1%}"
                )
                
                # News sentiment
                if 'news' in sent:
                    explanations.append(
                        f"- News Sentiment: {sent['news']:.1%}"
                    )
                
                # Social sentiment
                if 'social' in sent:
                    explanations.append(
                        f"- Social Media Sentiment: {sent['social']:.1%}"
                    )
            
            # Volume analysis
            if 'volume' in context:
                vol = context['volume']
                explanations.append(
                    f"- Volume: {vol.get('level', 'normal')} "
                    f"({vol.get('change', 0):.1%} change)"
                )
        
        return explanations
    
    def generate_summary(
        self,
        decision: str,
        confidence: float,
        key_points: List[str]
    ) -> str:
        """
        Generate concise summary.
        
        Args:
            decision: Trading decision
            confidence: Decision confidence
            key_points: List of key points
        
        Returns:
            Concise summary
        """
        summary = [
            f"DECISION: {decision}",
            f"CONFIDENCE: {confidence:.1%}",
            "\nKEY POINTS:"
        ]
        
        for point in key_points:
            summary.append(f"- {point}")
        
        return "\n".join(summary)
    
    def explain_change(
        self,
        old_analysis: Dict,
        new_analysis: Dict
    ) -> str:
        """
        Explain changes in analysis.
        
        Args:
            old_analysis: Previous analysis
            new_analysis: Current analysis
        
        Returns:
            Explanation of changes
        """
        changes = ["Analysis Changes:"]
        
        # Compare technical indicators
        if 'technical' in old_analysis and 'technical' in new_analysis:
            old_tech = old_analysis['technical']
            new_tech = new_analysis['technical']
            
            # Trend changes
            old_trend = old_tech.get('trend_strength', 0)
            new_trend = new_tech.get('trend_strength', 0)
            if abs(new_trend - old_trend) > 0.2:
                direction = "strengthened" if new_trend > old_trend else "weakened"
                changes.append(f"- Trend has {direction}")
            
            # Indicator changes
            if 'indicators' in old_tech and 'indicators' in new_tech:
                old_ind = old_tech['indicators']
                new_ind = new_tech['indicators']
                
                # RSI
                old_rsi = old_ind.get('rsi', 0)
                new_rsi = new_ind.get('rsi', 0)
                if abs(new_rsi - old_rsi) > 5:
                    changes.append(
                        f"- RSI changed from {old_rsi:.1f} to {new_rsi:.1f}"
                    )
        
        # Compare risk metrics
        if 'risk' in old_analysis and 'risk' in new_analysis:
            old_risk = old_analysis['risk']
            new_risk = new_analysis['risk']
            
            if old_risk.get('level') != new_risk.get('level'):
                changes.append(
                    f"- Risk level changed from {old_risk['level']} to "
                    f"{new_risk['level']}"
                )
        
        # Compare sentiment
        if 'context' in old_analysis and 'context' in new_analysis:
            old_ctx = old_analysis['context']
            new_ctx = new_analysis['context']
            
            if 'sentiment' in old_ctx and 'sentiment' in new_ctx:
                old_sent = old_ctx['sentiment']
                new_sent = new_ctx['sentiment']
                
                old_overall = old_sent.get('overall', 0)
                new_overall = new_sent.get('overall', 0)
                
                if abs(new_overall - old_overall) > 0.2:
                    direction = "improved" if new_overall > old_overall else "deteriorated"
                    changes.append(f"- Market sentiment has {direction}")
        
        if len(changes) == 1:
            changes.append("- No significant changes detected")
        
        return "\n".join(changes)
    
    def customize_explanation(
        self,
        base_explanation: str,
        style: str = 'detailed'
    ) -> str:
        """
        Customize explanation style.
        
        Args:
            base_explanation: Original explanation
            style: 'detailed', 'concise', or 'technical'
        
        Returns:
            Customized explanation
        """
        if style == 'concise':
            # Extract key points only
            lines = base_explanation.split('\n')
            key_points = [
                line for line in lines
                if line.startswith(('- ', 'DECISION:', 'CONFIDENCE:'))
            ]
            return "\n".join(key_points)
        
        elif style == 'technical':
            # Focus on technical details
            sections = base_explanation.split('\n\n')
            technical_sections = [
                section for section in sections
                if any(x in section for x in [
                    'Technical Analysis:',
                    'Feature Importance:',
                    'Risk Analysis:'
                ])
            ]
            return "\n\n".join(technical_sections)
        
        else:  # detailed
            return base_explanation
