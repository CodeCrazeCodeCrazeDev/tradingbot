"""
Phase 3: Neuro-Symbolic Reasoning - Chain of Thought
Multi-step reasoning for trading decisions
"""

import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ChainOfThoughtReasoner:
    """
    Multi-step reasoning process for trading decisions.
    Combines market analysis with logical inference.
    """
    
    def __init__(self):
        try:
            self.thought_history = []
            self.confidence_threshold = 0.7
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def reason_about_trade(self, market_state: Dict) -> Dict:
        """
        Multi-step reasoning about potential trade.
        
        Args:
            market_state: Current market conditions
        
        Returns:
            Decision with reasoning chain
        """
        try:
            thoughts = []
        
            # Step 1: Analyze current market regime
            regime = self._identify_regime(market_state)
            thoughts.append({
                'step': 'Market Regime Analysis',
                'conclusion': f"Market is in {regime} regime",
                'confidence': self._calculate_regime_confidence(market_state),
                'supporting_data': {
                    'volatility': market_state.get('volatility', 1.0),
                    'trend_strength': market_state.get('adx', 0)
                }
            })
        
            # Step 2: Technical Analysis
            tech_analysis = self._analyze_technicals(market_state)
            thoughts.append({
                'step': 'Technical Analysis',
                'conclusion': tech_analysis['conclusion'],
                'confidence': tech_analysis['confidence'],
                'supporting_data': tech_analysis['indicators']
            })
        
            # Step 3: Risk Assessment
            risk = self._assess_risk(market_state)
            thoughts.append({
                'step': 'Risk Assessment',
                'conclusion': f"Risk level is {risk['level']}",
                'confidence': risk['confidence'],
                'supporting_data': risk['metrics']
            })
        
            # Step 4: Consider Market Context
            context = self._analyze_context(market_state)
            thoughts.append({
                'step': 'Market Context',
                'conclusion': context['conclusion'],
                'confidence': context['confidence'],
                'supporting_data': context['factors']
            })
        
            # Step 5: Synthesize Decision
            decision = self._synthesize_decision(thoughts)
        
            # Record reasoning chain
            self.thought_history.append({
                'timestamp': np.datetime64('now'),
                'thoughts': thoughts,
                'decision': decision
            })
        
            return {
                'decision': decision['action'],
                'confidence': decision['confidence'],
                'reasoning_chain': thoughts,
                'explanation': self._generate_explanation(thoughts, decision)
            }
        except Exception as e:
            logger.error(f"Error in reason_about_trade: {e}")
            raise
    
    def _identify_regime(self, market_state: Dict) -> str:
        """Identify current market regime."""
        try:
            volatility = market_state.get('volatility', 1.0)
            adx = market_state.get('adx', 0)
        
            if volatility > 2.0:
                return 'high_volatility'
            elif adx > 25:
                return 'trending'
            elif volatility < 0.5:
                return 'low_volatility'
            else:
                return 'ranging'
        except Exception as e:
            logger.error(f"Error in _identify_regime: {e}")
            raise
    
    def _calculate_regime_confidence(self, market_state: Dict) -> float:
        """Calculate confidence in regime identification."""
        try:
            volatility = market_state.get('volatility', 1.0)
            adx = market_state.get('adx', 0)
        
            # Strong signals in either volatility or trend
            if volatility > 3.0 or adx > 30:
                return 0.9
            # Moderate signals
            elif volatility > 2.0 or adx > 25:
                return 0.7
            # Weak or mixed signals
            else:
                return 0.5
        except Exception as e:
            logger.error(f"Error in _calculate_regime_confidence: {e}")
            raise
    
    def _analyze_technicals(self, market_state: Dict) -> Dict:
        """Analyze technical indicators."""
        # Extract indicators
        try:
            rsi = market_state.get('rsi', 50)
            macd = market_state.get('macd', 0)
            sma_20 = market_state.get('sma_20', 0)
            sma_50 = market_state.get('sma_50', 0)
        
            # Count bullish signals
            bullish_signals = 0
            total_signals = 4
        
            if rsi < 30: bullish_signals += 1  # Oversold
            if macd > 0: bullish_signals += 1  # Positive momentum
            if sma_20 > sma_50: bullish_signals += 1  # Golden cross
            if market_state.get('trend', 0) > 0: bullish_signals += 1  # Uptrend
        
            # Determine bias
            if bullish_signals >= 3:
                conclusion = "Technical indicators suggest bullish momentum"
                confidence = bullish_signals / total_signals
            elif bullish_signals <= 1:
                conclusion = "Technical indicators suggest bearish momentum"
                confidence = (total_signals - bullish_signals) / total_signals
            else:
                conclusion = "Mixed technical signals"
                confidence = 0.5
        
            return {
                'conclusion': conclusion,
                'confidence': confidence,
                'indicators': {
                    'rsi': rsi,
                    'macd': macd,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'bullish_signals': bullish_signals,
                    'total_signals': total_signals
                }
            }
        except Exception as e:
            logger.error(f"Error in _analyze_technicals: {e}")
            raise
    
    def _assess_risk(self, market_state: Dict) -> Dict:
        """Assess current risk levels."""
        # Risk metrics
        try:
            volatility = market_state.get('volatility', 1.0)
            drawdown = market_state.get('drawdown', 0.0)
            correlation = market_state.get('correlation', 0.0)
        
            # Calculate risk score (0-1)
            risk_score = (
                0.4 * min(volatility / 3.0, 1.0) +  # Volatility component
                0.4 * min(abs(drawdown) / 0.1, 1.0) +  # Drawdown component
                0.2 * min(abs(correlation), 1.0)  # Correlation component
            )
        
            # Determine risk level
            if risk_score > 0.7:
                level = 'HIGH'
                confidence = 0.9
            elif risk_score > 0.3:
                level = 'MEDIUM'
                confidence = 0.7
            else:
                level = 'LOW'
                confidence = 0.8
        
            return {
                'level': level,
                'confidence': confidence,
                'metrics': {
                    'risk_score': risk_score,
                    'volatility': volatility,
                    'drawdown': drawdown,
                    'correlation': correlation
                }
            }
        except Exception as e:
            logger.error(f"Error in _assess_risk: {e}")
            raise
    
    def _analyze_context(self, market_state: Dict) -> Dict:
        """Analyze broader market context."""
        try:
            factors = {
                'market_sentiment': market_state.get('sentiment', 0),
                'economic_indicators': market_state.get('economic_score', 0),
                'news_impact': market_state.get('news_score', 0)
            }
        
            # Aggregate context score (-1 to 1)
            context_score = np.mean([
                factors['market_sentiment'],
                factors['economic_indicators'],
                factors['news_impact']
            ])
        
            # Interpret context
            if context_score > 0.3:
                conclusion = "Positive market context supports bullish bias"
                confidence = min(context_score + 0.5, 1.0)
            elif context_score < -0.3:
                conclusion = "Negative market context supports bearish bias"
                confidence = min(abs(context_score) + 0.5, 1.0)
            else:
                conclusion = "Neutral market context"
                confidence = 0.5
        
            return {
                'conclusion': conclusion,
                'confidence': confidence,
                'factors': factors
            }
        except Exception as e:
            logger.error(f"Error in _analyze_context: {e}")
            raise
    
    def _synthesize_decision(self, thoughts: List[Dict]) -> Dict:
        """Synthesize final decision from thought chain."""
        # Extract key signals
        try:
            regime = thoughts[0]['conclusion'].split()[-2]  # Extract regime name
            tech_bias = 'bullish' if 'bullish' in thoughts[1]['conclusion'] else 'bearish'
            risk_level = thoughts[2]['conclusion'].split()[-1]
            context = thoughts[3]['conclusion']
        
            # Decision rules
            if risk_level == 'HIGH':
                action = 'HOLD'
                reason = "High risk environment"
                confidence = thoughts[2]['confidence']
            
            elif regime == 'trending':
                if tech_bias == 'bullish' and 'positive' in context.lower():
                    action = 'BUY'
                    reason = "Strong bullish signals in trending market"
                    confidence = np.mean([t['confidence'] for t in thoughts])
                elif tech_bias == 'bearish' and 'negative' in context.lower():
                    action = 'SELL'
                    reason = "Strong bearish signals in trending market"
                    confidence = np.mean([t['confidence'] for t in thoughts])
                else:
                    action = 'HOLD'
                    reason = "Mixed signals in trending market"
                    confidence = 0.5
                
            else:  # ranging or other regimes
                if tech_bias == 'bullish' and thoughts[1]['confidence'] > 0.7:
                    action = 'BUY'
                    reason = "Strong bullish signals despite ranging market"
                    confidence = thoughts[1]['confidence'] * 0.8  # Reduce confidence
                elif tech_bias == 'bearish' and thoughts[1]['confidence'] > 0.7:
                    action = 'SELL'
                    reason = "Strong bearish signals despite ranging market"
                    confidence = thoughts[1]['confidence'] * 0.8
                else:
                    action = 'HOLD'
                    reason = "Insufficient conviction in ranging market"
                    confidence = 0.5
        
            return {
                'action': action,
                'reason': reason,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error in _synthesize_decision: {e}")
            raise
    
    def _generate_explanation(self, thoughts: List[Dict], decision: Dict) -> str:
        """Generate human-readable explanation of reasoning process."""
        try:
            explanation = f"Decision: {decision['action']} ({decision['confidence']:.1%} confidence)\n\n"
            explanation += "Reasoning process:\n\n"
        
            for thought in thoughts:
                explanation += f"{thought['step']}:\n"
                explanation += f"- {thought['conclusion']}\n"
                explanation += f"- Confidence: {thought['confidence']:.1%}\n"
                explanation += "- Supporting data:\n"
                for key, value in thought['supporting_data'].items():
                    explanation += f"  * {key}: {value}\n"
                explanation += "\n"
        
            explanation += f"Final decision based on: {decision['reason']}"
            return explanation
        except Exception as e:
            logger.error(f"Error in _generate_explanation: {e}")
            raise
    
    def get_recent_thoughts(self, n: int = 5) -> List[Dict]:
        """Get recent thought chains."""
        return self.thought_history[-n:]
    
    def analyze_decision_quality(self, thought_chain: List[Dict]) -> float:
        """Analyze quality of reasoning in a thought chain."""
        # Check confidence levels
        try:
            confidences = [thought['confidence'] for thought in thought_chain]
            avg_confidence = np.mean(confidences)
        
            # Check completeness
            expected_steps = {'Market Regime Analysis', 'Technical Analysis', 
                             'Risk Assessment', 'Market Context'}
            actual_steps = {thought['step'] for thought in thought_chain}
            completeness = len(actual_steps.intersection(expected_steps)) / len(expected_steps)
        
            # Check consistency
            consistent = True
            tech_bias = None
            for thought in thought_chain:
                if 'bullish' in thought['conclusion'].lower():
                    if tech_bias == 'bearish':
                        consistent = False
                        break
                    tech_bias = 'bullish'
                elif 'bearish' in thought['conclusion'].lower():
                    if tech_bias == 'bullish':
                        consistent = False
                        break
                    tech_bias = 'bearish'
        
            # Combine metrics
            quality_score = (
                0.4 * avg_confidence +
                0.3 * completeness +
                0.3 * float(consistent)
            )
        
            return quality_score
        except Exception as e:
            logger.error(f"Error in analyze_decision_quality: {e}")
            raise
